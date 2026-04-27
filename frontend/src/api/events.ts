import client from "./client";
import type { EventCreate, EventUpdate, EventResponse } from "../types/events";

export async function listEvents(): Promise<EventResponse[]> {
  const { data } = await client.get<EventResponse[]>("/events/");
  return data;
}

export async function getEvent(uid: string): Promise<EventResponse> {
  const { data } = await client.get<EventResponse>(`/events/${uid}`);
  return data;
}

export async function createEvent(event: EventCreate): Promise<EventResponse> {
  const { data } = await client.post<EventResponse>("/events/", event);
  return data;
}

export async function updateEvent(uid: string, updates: EventUpdate): Promise<EventResponse> {
  const { data } = await client.put<EventResponse>(`/events/${uid}`, updates);
  return data;
}

export async function setEventPlace(uid: string, placeUid: string): Promise<void> {
  await client.put(`/events/${uid}/place`, { place_uid: placeUid });
}

export async function removeEventPlace(uid: string): Promise<void> {
  await client.delete(`/events/${uid}/place`);
}
