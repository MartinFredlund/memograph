import client from "./client";
import type { PersonCreate, PersonUpdate, PersonResponse } from "../types/people";
import type { EventResponse } from "../types/events";
import type { PlaceResponse } from "../types/places";

export async function listPeople(): Promise<PersonResponse[]> {
  const { data } = await client.get<PersonResponse[]>("/people/");
  return data;
}

export async function getPerson(uid: string): Promise<PersonResponse> {
  const { data } = await client.get<PersonResponse>(`/people/${uid}`);
  return data;
}

export async function createPerson(person: PersonCreate): Promise<PersonResponse> {
  const { data } = await client.post<PersonResponse>("/people/", person);
  return data;
}

export async function updatePerson(uid: string, updates: PersonUpdate): Promise<PersonResponse> {
  const { data } = await client.put<PersonResponse>(`/people/${uid}`, updates);
  return data;
}

export async function getPersonEvents(uid: string): Promise<EventResponse[]> {
  const { data } = await client.get<EventResponse[]>(`/people/${uid}/events`);
  return data;
}

export async function getPersonPlaces(uid: string): Promise<PlaceResponse[]> {
  const { data } = await client.get<PlaceResponse[]>(`/people/${uid}/places`);
  return data;
}

export async function setBornAt(uid: string, placeUid: string): Promise<void> {
  await client.put(`/people/${uid}/born-at`, { place_uid: placeUid });
}

export async function removeBornAt(uid: string): Promise<void> {
  await client.delete(`/people/${uid}/born-at`);
}

export async function addAttended(uid: string, eventUid: string): Promise<void> {
  await client.post(`/people/${uid}/attended`, { event_uid: eventUid });
}

export async function removeAttended(uid: string, eventUid: string): Promise<void> {
  await client.delete(`/people/${uid}/attended/${eventUid}`);
}
