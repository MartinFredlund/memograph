export interface ImageResponse {
  uid: string;
  filename: string;
  object_key: string;
  content_type: string;
  size_bytes: number;
  uploaded_at: string;
  caption: string | null;
  taken_date: string | null;
}

export interface ImageDetail extends ImageResponse {
  tags: PersonTagResponse[];
  event: EventSummary | null;
  place: PlaceSummary | null;
}

export interface ImageUpdate {
  taken_date?: string | null;
  caption?: string | null;
}

export interface PersonTagCreate {
  person_uid: string;
  tag_x: number;
  tag_y: number;
}

export interface PersonTagResponse {
  person_uid: string;
  person_name: string;
  tag_x: number;
  tag_y: number;
}

export interface PersonTagSummary {
  person_uid: string;
  person_name: string;
}

export interface EventSummary {
  event_uid: string;
  event_name: string;
}

export interface PlaceSummary {
  place_uid: string;
  place_name: string;
}

export interface ImageListItem extends ImageResponse {
  tags: PersonTagSummary[];
  event: EventSummary | null;
  place: PlaceSummary | null;
}

export interface PaginatedImages {
  items: ImageListItem[];
  next_cursor: string | null;
}

export interface ImageListParams {
  person_uid?: string;
  event_uid?: string;
  place_uid?: string;
  cursor?: string;
  page_size?: number;
}

export interface ImageCountParams {
  person_uid?: string;
  event_uid?: string;
  place_uid?: string;
}
