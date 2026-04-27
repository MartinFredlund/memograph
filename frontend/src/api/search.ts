import client from "./client";
import type { SearchItem } from "../types/search";

export async function search(query: string): Promise<SearchItem[]> {
  const { data } = await client.get<SearchItem[]>("/search/", { params: { q: query } });
  return data;
}
