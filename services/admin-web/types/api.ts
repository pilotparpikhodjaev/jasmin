export interface Admin {
  id: string
  username: string
  email?: string
  role: string
  createdAt: string
}

export interface LoginResponse {
  token: string
  token_type: string
  expires_in: number
  refresh_token: string
}

export interface User {
  id: string
  username: string
  email: string
  role: string
  created_at: string
}

export interface Account {
  id: string
  name: string
  email: string
  type: "client" | "reseller"
  status: "active" | "suspended" | "inactive"
  balance: number
  sms_count: number
  created_at: string
  updated_at: string
}

export interface Operator {
  id: string
  name: string
  smpp_host: string
  smpp_port: number
  system_id: string
  password?: string
  system_type?: string
  status: "active" | "inactive"
  health_status?: "healthy" | "unhealthy" | "unknown"
  created_at: string
  updated_at: string
}

export interface OperatorFormData {
  name: string
  smpp_host: string
  smpp_port: number
  system_id: string
  password: string
  system_type?: string
  status: "active" | "inactive"
}

export interface DashboardStats {
  total_accounts: number
  total_messages_today: number
  total_revenue_today: number
  active_operators: number
  messages_per_day: Array<{ date: string; count: number }>
  revenue_per_day: Array<{ date: string; amount: number }>
  top_accounts: Array<{ id: string; name: string; usage: number }>
  recent_messages: Message[]
}

export interface Message {
  id: string
  from: string
  to: string
  content: string
  status: "pending" | "sent" | "delivered" | "failed"
  operatorId: string
  accountId: string
  createdAt: string
  deliveredAt?: string
}

export interface ModerationItem {
  id: string
  type: "message" | "account" | "content"
  status: "pending" | "approved" | "rejected"
  content: string
  metadata: Record<string, any>
  createdAt: string
  reviewedAt?: string
  reviewedBy?: string
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}
