<template>
  <view class="login-page">
    <view class="logo-area">
      <view class="logo-icon">🏥</view>
      <text class="logo-title">康复随访系统</text>
      <text class="logo-sub">青海子宫内膜癌智能诊疗平台</text>
    </view>

    <view class="form-area">
      <view class="form-item">
        <text class="label">患者编号</text>
        <input
          v-model="patientNo"
          placeholder="请输入您的患者编号 (如 EC202603010001)"
          class="input"
        />
      </view>

      <view class="form-item">
        <text class="label">手机号码</text>
        <input
          v-model="phone"
          type="number"
          maxlength="11"
          placeholder="请输入绑定的手机号"
          class="input"
        />
      </view>

      <button class="login-btn" :loading="loading" @tap="handleLogin">
        登 录
      </button>

      <view class="tips">
        <text class="tip-text">
          首次使用请联系您的主治医生获取患者编号
        </text>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      patientNo: '',
      phone: '',
      loading: false,
    };
  },

  methods: {
    async handleLogin() {
      if (!this.patientNo.trim()) {
        uni.showToast({ title: '请输入患者编号', icon: 'none' });
        return;
      }
      if (!this.phone || this.phone.length !== 11) {
        uni.showToast({ title: '请输入11位手机号', icon: 'none' });
        return;
      }

      this.loading = true;
      try {
        const res = await new Promise((resolve, reject) => {
          uni.request({
            url: 'http://127.0.0.1:8000/api/v1/patients/',
            method: 'GET',
            data: { page: 1, page_size: 1, keyword: this.patientNo.trim() },
            success: (r) => resolve(r.data),
            fail: reject,
          });
        });

        if (!res.success || !res.data.items || res.data.items.length === 0) {
          uni.showToast({ title: '未找到该患者编号', icon: 'none' });
          return;
        }

        const patient = res.data.items[0];

        if (patient.phone && patient.phone !== this.phone) {
          uni.showToast({ title: '手机号与登记信息不符', icon: 'none' });
          return;
        }

        uni.setStorageSync('patient_id', patient.id);
        uni.setStorageSync('patient_no', patient.patient_no);
        uni.setStorageSync('patient_name', patient.name);
        uni.setStorageSync('patient_token', 'patient_session');

        uni.showToast({ title: '登录成功', icon: 'success' });
        setTimeout(() => {
          uni.reLaunch({ url: '/pages/index/index' });
        }, 800);
      } catch (err) {
        console.error(err);
        uni.showToast({ title: '网络错误，请稍后重试', icon: 'none' });
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #667eea 0%, #764ba2 50%, #f5f5f5 50%);
  padding: 0 40rpx;
}
.logo-area {
  padding-top: 120rpx;
  text-align: center;
  color: white;
}
.logo-icon { font-size: 100rpx; }
.logo-title { display: block; font-size: 44rpx; font-weight: bold; margin: 20rpx 0 10rpx; }
.logo-sub { display: block; font-size: 26rpx; opacity: 0.85; }
.form-area {
  background: white;
  border-radius: 24rpx;
  padding: 50rpx 40rpx;
  margin-top: 60rpx;
  box-shadow: 0 8rpx 30rpx rgba(0,0,0,0.12);
}
.form-item { margin-bottom: 36rpx; }
.label { display: block; font-size: 28rpx; color: #333; font-weight: 500; margin-bottom: 12rpx; }
.input {
  border: 1px solid #e0e0e0;
  border-radius: 12rpx;
  padding: 20rpx 24rpx;
  font-size: 28rpx;
  width: 100%;
  box-sizing: border-box;
}
.login-btn {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 12rpx;
  font-size: 32rpx;
  padding: 24rpx 0;
  margin-top: 20rpx;
}
.tips { margin-top: 30rpx; text-align: center; }
.tip-text { font-size: 24rpx; color: #999; }
</style>
