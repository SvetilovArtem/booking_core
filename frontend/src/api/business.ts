/** API-методы для работы с салонами */
import api from './index';
import type { Business } from '../types';

export const businessesApi = {
  getAll: () => api.get<Business[]>('/businesses/'),
  create: (data: { name: string; timezone?: string }) =>
    api.post<Business>('/businesses/', data),
  update: (id: number, data: { name?: string; timezone?: string; is_active?: boolean }) =>
    api.patch<Business>(`/businesses/${id}`, data),
  delete: (id: number) => api.delete(`/businesses/${id}`),
};