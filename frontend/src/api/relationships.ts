import client from "./client";
import type { RelationshipCreate, RelationshipUpdate, RelationshipResponse } from "../types/relationships";

export async function getPersonRelationships(personUid: string): Promise<RelationshipResponse[]> {
  const { data } = await client.get<RelationshipResponse[]>(`/people/${personUid}/relationships`);
  return data;
}

export async function createRelationship(rel: RelationshipCreate): Promise<RelationshipResponse> {
  const { data } = await client.post<RelationshipResponse>("/relationships", rel);
  return data;
}

export async function updateRelationship(uid: string, updates: RelationshipUpdate): Promise<RelationshipResponse> {
  const { data } = await client.put<RelationshipResponse>(`/relationships/${uid}`, updates);
  return data;
}

export async function deleteRelationship(uid: string): Promise<void> {
  await client.delete(`/relationships/${uid}`);
}
