export type RelationshipCategory = "PARENT_OF" | "PARTNER_OF" | "SOCIAL";

export interface RelationshipCreate {
  from_uid: string;
  to_uid: string;
  category: RelationshipCategory;
  since?: string | null;
  context?: string | null;
  social_type?: string | null;
}

export interface RelationshipUpdate {
  since?: string | null;
  context?: string | null;
}

export interface RelationshipResponse {
  uid: string;
  from_uid: string;
  to_uid: string;
  category: RelationshipCategory;
  since: string | null;
  context: string | null;
  social_type: string | null;
}
