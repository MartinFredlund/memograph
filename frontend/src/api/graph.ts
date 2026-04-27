import client from "./client";
import type { GraphResponse } from "../types/graph";

export async function getGraph(): Promise<GraphResponse> {
  const { data } = await client.get<GraphResponse>("/graph/");
  return data;
}

export async function getNeighborhood(uid: string): Promise<GraphResponse> {
  const { data } = await client.get<GraphResponse>(`/graph/neighborhood/${uid}`);
  return data;
}
