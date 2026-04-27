export interface PersonCreate {
  name: string;
  birth_date?: string | null;
  death_date?: string | null;
  gender?: string | null;
  nickname?: string | null;
  description?: string | null;
}

export interface PersonUpdate {
  name?: string | null;
  birth_date?: string | null;
  death_date?: string | null;
  gender?: string | null;
  nickname?: string | null;
  description?: string | null;
}

export interface PersonResponse {
  uid: string;
  name: string;
  birth_date: string | null;
  death_date: string | null;
  gender: string | null;
  nickname: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}
