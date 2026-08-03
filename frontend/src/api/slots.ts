/** API-методы для работы со слотами */
import api from './index';

export interface DayStats {
  date: string;
  available: number;
  booked: number;
  total: number;
}

export interface SlotBulkPayload {
  master_id: number;
  business_id: number;
  date_from: string;
  date_to: string;
  times: string[];
  duration_minutes: number;
}

export const slotsApi = {
  getStats: (params?: { master_id?: number; business_id?: number; date_from?: string; date_to?: string }) =>
    api.get<DayStats[]>('/slots/stats', { params }),
  createBulk: (data: SlotBulkPayload) =>
    api.post<{ created: number; skipped: number }>('/slots/bulk', data),
  getAll: (params?: { master_id?: number; business_id?: number; date_from?: string; date_to?: string }) =>
    api.get('/slots/', { params }),
  delete: (id: number) => api.delete(`/slots/${id}`),
};