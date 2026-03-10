const BASE_URL = 'http://127.0.0.1:8000/api/v1';

function getToken() {
  return uni.getStorageSync('patient_token') || '';
}

function getPatientId() {
  return uni.getStorageSync('patient_id') || 0;
}

function request(url, method = 'GET', data = {}) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getToken()}`,
      },
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data);
        } else if (res.statusCode === 401) {
          uni.removeStorageSync('patient_token');
          uni.removeStorageSync('patient_id');
          uni.reLaunch({ url: '/pages/login/login' });
          reject(new Error('未授权'));
        } else {
          const msg = res.data?.detail || res.data?.message || '请求失败';
          uni.showToast({ title: msg, icon: 'none' });
          reject(new Error(msg));
        }
      },
      fail: (err) => {
        uni.showToast({ title: '网络错误', icon: 'none' });
        reject(err);
      },
    });
  });
}

export default {
  getPatientId,

  getMyTasks(status) {
    const pid = getPatientId();
    let url = `/followup/tasks/patient/${pid}`;
    if (status) url += `?status=${status}`;
    return request(url);
  },

  getMyPlans() {
    const pid = getPatientId();
    return request(`/followup/plans/patient/${pid}`);
  },

  submitRecord(data) {
    return request('/followup/records', 'POST', data);
  },

  getPatientInfo() {
    const pid = getPatientId();
    return request(`/patients/${pid}`);
  },

  getMyAIResults() {
    const pid = getPatientId();
    return request(`/ai/results/patient/${pid}`);
  },

  uploadFile(filePath) {
    const pid = getPatientId();
    return new Promise((resolve, reject) => {
      uni.uploadFile({
        url: `${BASE_URL}/images/upload/${pid}`,
        filePath,
        name: 'files',
        header: { Authorization: `Bearer ${getToken()}` },
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(JSON.parse(res.data));
          } else {
            reject(new Error('上传失败'));
          }
        },
        fail: reject,
      });
    });
  },
};
