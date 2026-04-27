import client from "./client";
import type {
  ImageDetail,
  ImageUpdate,
  ImageListParams,
  ImageListItem,
  PaginatedImages,
  ImageCountParams,
  PersonTagCreate,
  PersonTagResponse,
  ImageResponse,
} from "../types/images";

export async function uploadImages(files: File[]): Promise<ImageResponse[]> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const { data } = await client.post<ImageResponse[]>("/images/", form);
  return data;
}

export async function getImage(uid: string): Promise<ImageDetail> {
  const { data } = await client.get<ImageDetail>(`/images/${uid}`);
  return data;
}

export async function updateImage(uid: string, updates: ImageUpdate): Promise<ImageDetail> {
  const { data } = await client.put<ImageDetail>(`/images/${uid}`, updates);
  return data;
}

export async function deleteImage(uid: string): Promise<void> {
  await client.delete(`/images/${uid}`);
}

export async function rotateImage(uid: string, degrees: 90 | 180 | 270): Promise<ImageResponse> {
  const { data } = await client.post<ImageResponse>(`/images/${uid}/rotate`, { degrees });
  return data;
}

export async function listImages(params: ImageListParams = {}): Promise<PaginatedImages> {
  const { data } = await client.get<PaginatedImages>("/images/", { params });
  return data;
}

export async function getImageCount(params: ImageCountParams = {}): Promise<number> {
  const { data } = await client.get<{ count: number }>("/images/count", { params });
  return data.count;
}

export async function getDownloadUrl(uid: string): Promise<string> {
  const { data } = await client.get<{ url: string }>(`/images/${uid}/download`);
  return data.url;
}

export async function addTag(uid: string, tag: PersonTagCreate): Promise<PersonTagResponse> {
  const { data } = await client.post<PersonTagResponse>(`/images/${uid}/tags`, tag);
  return data;
}

export async function removeTag(uid: string, personUid: string): Promise<void> {
  await client.delete(`/images/${uid}/tags/${personUid}`);
}

export async function setImagePlace(uid: string, placeUid: string): Promise<void> {
  await client.put(`/images/${uid}/place`, { place_uid: placeUid });
}

export async function removeImagePlace(uid: string): Promise<void> {
  await client.delete(`/images/${uid}/place`);
}

export async function setImageEvent(uid: string, eventUid: string): Promise<void> {
  await client.put(`/images/${uid}/event`, { event_uid: eventUid });
}

export async function removeImageEvent(uid: string): Promise<void> {
  await client.delete(`/images/${uid}/event`);
}
