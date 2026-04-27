import { useQuery } from "@tanstack/react-query";
import * as api from "../api/graph";

export function useGraph() {
  return useQuery({ queryKey: ["graph"], queryFn: api.getGraph });
}

export function useNeighborhood(uid: string) {
  return useQuery({
    queryKey: ["graph", "neighborhood", uid],
    queryFn: () => api.getNeighborhood(uid),
  });
}
