import axios from 'axios';

const api = axios.create({
  // In production (unified domain), we use relative paths.
  // We set baseURL to empty string to avoid "Double /api" (e.g. /api/api/upload)
  baseURL: import.meta.env.VITE_API_URL !== undefined && import.meta.env.VITE_API_URL !== ''
           ? import.meta.env.VITE_API_URL 
           : (typeof window !== 'undefined' && (window.location.hostname.includes('web.app') || window.location.hostname.includes('run.app')) 
              ? '' 
              : 'http://localhost:8080'),
  timeout: 120000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('fairlens_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const token = localStorage.getItem('fairlens_token');
    if (err.response?.status === 401 && token !== 'demo_token') {
      localStorage.clear();
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

/* ── API Endpoints ── */

export const googleAuth = async (idToken) => {
  const res = await api.post('/api/auth/google', { id_token: idToken });
  return res.data;
};

export const runFullAudit = async (fileId, targetColumn, sensitiveColumns, positiveLabel = 1) => {
  const res = await api.post('/api/audit/full', {
    file_id: fileId,
    target_column: targetColumn,
    sensitive_columns: sensitiveColumns,
    positive_label: positiveLabel,
  });
  return res.data;
};

export const getAuditReport = async (fileId) => {
  const res = await api.get(`/api/audit/${fileId}/report`);
  return res.data;
};

export const getAuditHistory = async () => {
  const res = await api.get('/api/history/audits');
  return res.data;
};

export const uploadCSV = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const detectAuditConfig = async (fileId) => {
  const res = await api.post('/api/templates/detect', { file_id: fileId });
  return res.data;
};

export const generatePDFReport = async (auditData, datasetName) => {
  const res = await api.post('/api/report/generate', 
    { audit_data: auditData, dataset_name: datasetName },
    { responseType: 'blob' }
  );
  return res.data;
};

export const compareAI = async (fileId, targetColumn, sensitiveColumns, positiveLabel = 1) => {
  const res = await api.post('/api/audit/compare-ai', {
    file_id: fileId,
    target_column: targetColumn,
    sensitive_columns: sensitiveColumns,
    positive_label: positiveLabel,
  });
  return res.data;
};

export const applyMitigation = async (fileId, method, targetColumn, sensitiveAttribute) => {
  const res = await api.post('/api/audit/mitigate', {
    file_id: fileId,
    method: method,
    target_column: targetColumn,
    sensitive_attribute: sensitiveAttribute
  });
  return res.data;
};

export default api;
