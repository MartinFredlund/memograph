export interface EventCreate {
  name: string;
  start_date?: string | null;
  end_date?: string | null;
  description?: string | null;
}

export interface EventUpdate {
  name?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  description?: string | null;
}

export interface EventResponse {
  uid: string;
  name: string;
  start_date: string | null;
  end_date: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
  derived?: boolean | null;
  explicit?: boolean | null;
}
