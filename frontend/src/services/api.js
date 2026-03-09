/**
 * ObraHunter - API Service
 * Multi-usuário com JWT auth + notificações in-app
 */
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({ baseURL: API_URL });

// Interceptor: adiciona token JWT em toda request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('obrahunter_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Interceptor: redireciona para login se 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('obrahunter_token');
      localStorage.removeItem('obrahunter_user');
      window.location.reload();
    }
    return Promise.reject(err);
  }
);

// Auth
export const authAPI = {
  login: (email, senha) => api.post('/auth/login', { email, senha }),
  setup: (data) => api.post('/auth/setup', data),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/users/me'),
  updateMe: (data) => api.patch('/users/me', data),
  listUsers: () => api.get('/users'),
  toggleUser: (id) => api.patch(`/users/${id}/toggle`),
};

// Obras
export const obrasAPI = {
  listar: (params = {}) => api.get('/obras', { params }),
  detalhe: (id) => api.get(`/obras/${id}`),
  atualizar: (id, data) => api.patch(`/obras/${id}`, data),
};

// Decisores
export const decisoresAPI = {
  listarPorObra: (obraId) => api.get(`/obras/${obraId}/decisores`),
  atualizar: (id, data) => api.patch(`/decisores/${id}`, data),
};

// Interações
export const interacoesAPI = {
  criar: (data) => api.post('/interacoes', data),
  listarPorObra: (obraId) => api.get(`/obras/${obraId}/interacoes`),
};

// Buscas Automáticas
export const buscasAPI = {
  listar: () => api.get('/buscas'),
  criar: (data) => api.post('/buscas', data),
  toggle: (id) => api.patch(`/buscas/${id}/toggle`),
  executar: (id) => api.post(`/buscas/${id}/executar`),
  execucoes: (id) => api.get(`/buscas/${id}/execucoes`),
  manual: (filtros) => api.post('/busca-manual', filtros),
};

// Dashboard
export const dashboardAPI = {
  stats: () => api.get('/dashboard'),
  alertas: (limit = 20) => api.get('/alertas/recentes', { params: { limit } }),
};

// Notificações (in-app)
export const notificacoesAPI = {
  listar: (params = {}) => api.get('/notificacoes', { params }),
  resumo: () => api.get('/notificacoes/resumo'),
  marcarLida: (id) => api.patch(`/notificacoes/${id}/lida`),
  marcarTodasLidas: () => api.post('/notificacoes/marcar-todas-lidas'),
};

export default api;
