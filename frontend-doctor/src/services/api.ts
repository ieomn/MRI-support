/**
 * API请求封装
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { message } from 'antd';

// 创建axios实例
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8888/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加token
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data;
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      
      if (status === 401) {
        message.error('未授权，请重新登录');
        localStorage.removeItem('token');
        window.location.href = '/login';
      } else if (status === 404) {
        message.error('请求的资源不存在');
      } else if (status === 500) {
        message.error('服务器错误');
      } else {
        message.error(data?.message || '请求失败');
      }
    } else {
      message.error('网络错误');
    }
    
    return Promise.reject(error);
  }
);

// ==================== 患者管理API ====================

export interface Patient {
  id: number;
  patient_no: string;
  name: string;
  gender: string;
  age?: number;
  phone?: string;
  hospital?: string;
  diagnosis?: string;
  stage?: string;
}

export interface PatientCreateData {
  name: string;
  gender: 'male' | 'female' | 'other';
  birth_date?: string;
  phone?: string;
  address?: string;
  admission_date?: string;
  hospital?: string;
  diagnosis?: string;
  stage?: string;
}

export const patientAPI = {
  // 获取患者列表
  list: (params: { page: number; page_size: number; keyword?: string }) =>
    api.get('/patients/', { params }),
  
  // 获取患者详情
  get: (id: number) => api.get(`/patients/${id}`),
  
  // 创建患者
  create: (data: PatientCreateData) => api.post('/patients/', data),
  
  // 更新患者
  update: (id: number, data: Partial<PatientCreateData>) =>
    api.put(`/patients/${id}`, data),
  
  // 删除患者
  delete: (id: number) => api.delete(`/patients/${id}`),
};

// ==================== 影像管理API ====================

export const imageAPI = {
  // 上传DICOM文件
  upload: (patientId: number, files: FileList) => {
    const formData = new FormData();
    Array.from(files).forEach((file) => {
      formData.append('files', file);
    });
    
    return api.post(`/images/upload/${patientId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  // 获取患者影像列表
  getPatientImages: (patientId: number) =>
    api.get(`/images/patient/${patientId}`),
  
  // 获取影像元数据
  getMetadata: (seriesId: number) =>
    api.get(`/images/series/${seriesId}/metadata`),
  
  // 获取下载URL
  getDownloadUrl: (seriesId: number) =>
    api.get(`/images/series/${seriesId}/download-url`),
};

// ==================== 标注管理API ====================

export const annotationAPI = {
  // 创建标注
  create: (data: {
    series_id: number;
    patient_id: number;
    annotation_type: string;
    annotation_data: any;
    slice_index?: number;
  }) => api.post('/annotations/', data),
  
  // 获取影像序列的标注
  getSeriesAnnotations: (seriesId: number) =>
    api.get(`/annotations/series/${seriesId}`),
};

// ==================== AI分析API ====================

export const aiAPI = {
  // 运行分割
  runSegmentation: (data: { series_id: number; threshold?: number }) =>
    api.post('/ai/segment', data),
  
  // 预后预测
  predictPrognosis: (data: { patient_id: number; clinical_data: any }) =>
    api.post('/ai/predict-prognosis', data),
  
  // 获取患者AI结果
  getPatientResults: (patientId: number) =>
    api.get(`/ai/results/patient/${patientId}`),
};

// ==================== 随访管理API ====================

export const followupAPI = {
  // 创建随访计划
  createPlan: (data: {
    patient_id: number;
    plan_name: string;
    start_date: string;
    schedule_config: any[];
  }) => api.post('/followup/plans', data),
  
  // 获取患者随访计划
  getPatientPlans: (patientId: number) =>
    api.get(`/followup/plans/patient/${patientId}`),
  
  // 获取患者随访任务
  getPatientTasks: (patientId: number, status?: string) =>
    api.get(`/followup/tasks/patient/${patientId}`, { params: { status } }),
  
  // 获取随访看板
  getDashboard: () => api.get('/followup/dashboard'),
};

export default api;

