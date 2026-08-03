export interface Business {
  id: number;
  name: string;
  timezone: string;
  is_active: boolean;
}

export interface Client {
  id: number;
  name: string | null;
  telegram_id: number;
  phone: string | null;
  is_blocked: boolean;
  created_at: string;
}

export interface Master {
  id: number;
  name: string;
  phone: string | null;
  telegram_id: number | null;
  is_blocked: boolean;
  created_at: string;
  service_ids: number[];
  business_ids: number[];
}

export interface Service {
  id: number;
  name: string;
  price: number;
  created_at: string;
}

export interface Slot {
  id: number;
  master_id: number;
  business_id: number;
  date: string;
  start_time: string;
  end_time: string;
  status: 'available' | 'booked' | 'cancelled' | 'blocked';
  created_at: string;
}

export interface Order {
  id: number;
  client_id: number;
  slot_id: number;
  service_id: number;
  business_id: number;
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed' | 'no_show';
  number: string | null;
  cancel_reason: string | null;
  created_at: string;
}

export interface Admin {
  id: number;
  name: string;
  phone: string | null;
  telegram_id: number | null;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface DashboardStats {
  total_orders: number;
  orders_today: number;
  orders_week: number;
  orders_month: number;
  orders_by_status: Record<string, number>;
  total_revenue: number;
  revenue_month: number;
  total_clients: number;
  total_masters: number;
  total_services: number;
  total_businesses: number;
}