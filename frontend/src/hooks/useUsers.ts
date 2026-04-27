import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "../api/auth";
import type { UpdateUser } from "../api/auth";

export function useUsers() {
  return useQuery({ queryKey: ["users"], queryFn: api.listUsers });
}

export function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ uid, updates }: { uid: string; updates: UpdateUser }) =>
      api.updateUser(uid, updates),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
}
