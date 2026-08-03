import api from './index';
import type { Client } from '../types';

export const clientsApi = {
  getAll: () => api.get<Client[]>('/clients/'),
  create: (data: { name?: string; telegram_id: number; phone?: string }) =>
    api.post<Client>('/clients/', data),
  update: (id: number, data: { name?: string; phone?: string; is_blocked?: boolean }) =>
    api.patch<Client>(`/clients/${id}`, data),
  delete: (id: number) => api.delete(`/clients/${id}`),
};