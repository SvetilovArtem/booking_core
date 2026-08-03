/** API-методы для работы с услугами */
import api from './index';
import type { Service } from '../types';

export const servicesApi = {
  getAll: () => api.get<Service[]>('/services/'),
  create: (data: { name: string; price: number }) =>
    api.post<Service>('/services/', data),
  update: (id: number, data: { name?: string; price?: number }) =>
    api.put<Service>(`/services/${id}`, data),
  delete: (id: number) => api.delete(`/services/${id}`),
};