import client from "./client";
import type { PlaceCreate, PlaceUpdate, PlaceResponse } from "../types/places";

export async function listPlaces(): Promise<PlaceResponse[]> {
  const { data } = await client.get<PlaceResponse[]>("/places/");
  return data;
}

export async function getPlace(uid: string): Promise<PlaceResponse> {
  const { data } = await client.get<PlaceResponse>(`/places/${uid}`);
  return data;
}

export async function createPlace(place: PlaceCreate): Promise<PlaceResponse> {
  const { data } = await client.post<PlaceResponse>("/places/", place);
  return data;
}

export async function updatePlace(uid: string, updates: PlaceUpdate): Promise<PlaceResponse> {
  const { data } = await client.put<PlaceResponse>(`/places/${uid}`, updates);
  return data;
}
