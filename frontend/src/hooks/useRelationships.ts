import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "../api/relationships";
import type { RelationshipCreate, RelationshipUpdate } from "../types/relationships";

export function usePersonRelationships(personUid: string) {
  return useQuery({
    queryKey: ["relationships", personUid],
    queryFn: () => api.getPersonRelationships(personUid),
  });
}

export function useCreateRelationship() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (rel: RelationshipCreate) => api.createRelationship(rel),
    onSuccess: (_data, rel) => {
      qc.invalidateQueries({ queryKey: ["relationships", rel.from_uid] });
      qc.invalidateQueries({ queryKey: ["relationships", rel.to_uid] });
      qc.invalidateQueries({ queryKey: ["graph"] });
    },
  });
}

export function useUpdateRelationship() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ uid, updates }: { uid: string; updates: RelationshipUpdate }) =>
      api.updateRelationship(uid, updates),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["relationships"] }),
  });
}

export function useDeleteRelationship() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (uid: string) => api.deleteRelationship(uid),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["relationships"] });
      qc.invalidateQueries({ queryKey: ["graph"] });
    },
  });
}
