import { useQuery } from "@tanstack/react-query";
import * as api from "../api/search";

export function useSearch(query: string) {
  return useQuery({
    queryKey: ["search", query],
    queryFn: () => api.search(query),
    enabled: query.length >= 2,
  });
}
