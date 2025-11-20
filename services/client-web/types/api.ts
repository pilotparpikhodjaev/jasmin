export interface User {
  id: string;
  username: string;
  email: string;
  name?: string;
  balance?: number;
  sms_count?: number;
  role: "admin" | "client";
  createdAt: string;
  updatedAt: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  token_type: string;
  expires_in: number;
  refresh_token: string;
  user: User;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface SMSMessage {
  message_id: string;
  mobile_phone: string;
  message: string;
  from?: string;
  status: "DELIVRD" | "UNDELIV" | "PENDING" | "EXPIRED" | "REJECTED" | "FAILED";
  created_at: string;
  delivered_at?: string;
  price: number;
  message_parts?: number;
  encoding?: "GSM7" | "UCS2";
}

export interface SMSCheckResponse {
  message_parts: number;
  encoding: "GSM7" | "UCS2";
  price_estimate: number;
  message_length: number;
}

export interface SMSSendRequest {
  mobile_phone: string;
  message: string;
  from: string;
}

export interface SMSSendResponse {
  request_id: string;
  message_id: string;
  status: string;
  sms_count: number;
  price: number;
  balance_after: number;
}

export interface SMSBatchRequest {
  messages: Array<{
    mobile_phone: string;
    message: string;
    from?: string;
  }>;
}

export interface UserMessagesRequest {
  page?: number;
  page_size?: number;
  status?: string;
  start_date?: string;
  end_date?: string;
}

export interface MessageStats {
  total: number;
  sent: number;
  delivered: number;
  failed: number;
  pending: number;
}

export interface Account {
  balance: number;
  currency: string;
  smsCredits: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
