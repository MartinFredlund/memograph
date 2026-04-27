export interface PlaceCreate {
  name: string;
  address?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  description?: string | null;
}

export interface PlaceUpdate {
  name?: string | null;
  address?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  description?: string | null;
}

export interface PlaceResponse {
  uid: string;
  name: string;
  address: string | null;
  latitude: number | null;
  longitude: number | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}
