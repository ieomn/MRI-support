/**
 * API 请求封装
 */
import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { message } from 'antd';

const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
});

const longApi: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 180_000,
  headers: { 'Content-Type': 'application/json' },
});

function attachInterceptors(instance: AxiosInstance) {
  instance.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error),
  );

  instance.interceptors.response.use(
    (response: AxiosResponse) => response.data,
    (error) => {
      if (error.response) {
        const { status, data } = error.response;
        if (status === 401) {
          message.error('未授权，请重新登录');
          localStorage.removeItem('token');
          window.location.href = '/login';
        } else if (status === 502) {
          message.error('AI 推理服务暂不可用，请稍后重试');
        } else if (status === 500) {
          message.error(data?.detail || '服务器错误');
        } else {
          message.error(data?.detail || data?.message || '请求失败');
        }
      } else if (error.code === 'ECONNABORTED') {
        message.error('请求超时，AI 分析可能需要较长时间');
      } else {
        message.error('网络错误，请检查连接');
      }
      return Promise.reject(error);
    },
  );
}

attachInterceptors(api);
attachInterceptors(longApi);

// ==================== 类型定义 ====================

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

export interface MedGemmaReport {
  series_id?: number;
  patient_id: number;
  report: string;
  inference_time: number;
  model_id: string;
}

export interface MedGemmaAnswer {
  answer: string;
  inference_time: number;
}

// ==================== 患者管理 API ====================

export const patientAPI = {
  list: (params: { page: number; page_size: number; keyword?: string }) =>
    api.get('/patients/', { params }),

  get: (id: number) => api.get(`/patients/${id}`),

  create: (data: PatientCreateData) => api.post('/patients/', data),

  update: (id: number, data: Partial<PatientCreateData>) =>
    api.put(`/patients/${id}`, data),

  delete: (id: number) => api.delete(`/patients/${id}`),
};

// ==================== 影像管理 API ====================

export const imageAPI = {
  upload: (patientId: number, files: FileList) => {
    const formData = new FormData();
    Array.from(files).forEach((file) => formData.append('files', file));
    return api.post(`/images/upload/${patientId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120_000,
    });
  },

  getPatientImages: (patientId: number) =>
    api.get(`/images/patient/${patientId}`),

  getMetadata: (seriesId: number) =>
    api.get(`/images/series/${seriesId}/metadata`),

  getDownloadUrl: (seriesId: number) =>
    api.get(`/images/series/${seriesId}/download-url`),
};

// ==================== 标注管理 API ====================

export const annotationAPI = {
  create: (data: {
    series_id: number;
    patient_id: number;
    annotation_type: string;
    annotation_data: any;
    slice_index?: number;
  }) => api.post('/annotations/', data),

  getSeriesAnnotations: (seriesId: number) =>
    api.get(`/annotations/series/${seriesId}`),
};

// ==================== AI 分析 API（U-Net / 传统回归）====================

export const aiAPI = {
  runSegmentation: (data: { series_id: number; threshold?: number }) =>
    longApi.post('/ai/segment', data),

  predictPrognosis: (data: { patient_id: number; clinical_data: any }) =>
    longApi.post('/ai/predict-prognosis', data),

  getPatientResults: (patientId: number) =>
    api.get(`/ai/results/patient/${patientId}`),
};

// ==================== MedGemma API ====================

export const medgemmaAPI = {
  health: () => api.get('/ai/medgemma/health'),

  analyzeImage: (data: {
    series_id: number;
    patient_id: number;
    clinical_context?: string;
    prompt?: string;
  }) => longApi.post('/ai/medgemma/analyze-image', data),

  analyzePrognosis: (data: {
    patient_id: number;
    clinical_data: Record<string, any>;
  }) => longApi.post('/ai/medgemma/analyze-prognosis', data),

  ask: (data: {
    question: string;
    patient_id?: number;
    image_base64?: string;
  }) => longApi.post('/ai/medgemma/ask', data),
};

// ==================== 随访管理 API ====================

export const followupAPI = {
  createPlan: (data: {
    patient_id: number;
    plan_name: string;
    start_date: string;
    schedule_config: any[];
  }) => api.post('/followup/plans', data),

  getPatientPlans: (patientId: number) =>
    api.get(`/followup/plans/patient/${patientId}`),

  getPatientTasks: (patientId: number, status?: string) =>
    api.get(`/followup/tasks/patient/${patientId}`, { params: { status } }),

  getDashboard: () => api.get('/followup/dashboard'),
};

export default api;
