export type Template = {
  id: string;
  account_id: string;
  name: string;
  channel: string;
  category?: string | null;
  content: string;
  variables?: string[];
  status: string;
  admin_comment?: string | null;
  last_submitted_at: string;
  approved_at?: string | null;
  updated_at: string;
};

export type Balance = {
  account_id: string;
  balance: string;
  credit_limit: string;
  currency: string;
  updated_at: string;
};

export type AuthProfile = {
  account_id: string;
  account_name: string;
  currency: string;
  balance: string;
  credit_limit: string;
  rate_limit_rps?: number | null;
  allowed_ips?: string[] | null;
};

