/** API-методы для работы с мастерами */
import api from './index';
import type { Master, Service, Business } from '../types';

export interface MasterPayload {
  name: string;
  phone?: string;
  telegram_id: number;
  service_ids: number[];
  business_ids: number[];
}

export const mastersApi = {
  getAll: () => api.get<Master[]>('/masters/'),
  create: (data: MasterPayload) => api.post<Master>('/masters/', data),
  update: (id: number, data: Partial<MasterPayload> & { is_blocked?: boolean }) =>
    api.patch<Master>(`/masters/${id}`, data),
  delete: (id: number) => api.delete(`/masters/${id}`),
};

export const selectorsApi = {
  getServices: () => api.get<Service[]>('/services/'),
  getBusinesses: () => api.get<Business[]>('/businesses/'),
};