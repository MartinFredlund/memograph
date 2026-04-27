import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "../api/places";
import type { PlaceCreate, PlaceUpdate } from "../types/places";

export function usePlaces() {
  return useQuery({ queryKey: ["places"], queryFn: api.listPlaces });
}

export function usePlace(uid: string) {
  return useQuery({ queryKey: ["places", uid], queryFn: () => api.getPlace(uid) });
}

export function useCreatePlace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (place: PlaceCreate) => api.createPlace(place),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["places"] }),
  });
}

export function useUpdatePlace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ uid, updates }: { uid: string; updates: PlaceUpdate }) =>
      api.updatePlace(uid, updates),
    onSuccess: (_data, { uid }) => {
      qc.invalidateQueries({ queryKey: ["places"] });
      qc.invalidateQueries({ queryKey: ["places", uid] });
    },
  });
}
