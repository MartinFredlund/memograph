import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "../api/events";
import type { EventCreate, EventUpdate } from "../types/events";

export function useEvents() {
  return useQuery({ queryKey: ["events"], queryFn: api.listEvents });
}

export function useEvent(uid: string) {
  return useQuery({ queryKey: ["events", uid], queryFn: () => api.getEvent(uid) });
}

export function useCreateEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (event: EventCreate) => api.createEvent(event),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["events"] }),
  });
}

export function useUpdateEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ uid, updates }: { uid: string; updates: EventUpdate }) =>
      api.updateEvent(uid, updates),
    onSuccess: (_data, { uid }) => {
      qc.invalidateQueries({ queryKey: ["events"] });
      qc.invalidateQueries({ queryKey: ["events", uid] });
    },
  });
}

export function useSetEventPlace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ uid, placeUid }: { uid: string; placeUid: string }) =>
      api.setEventPlace(uid, placeUid),
    onSuccess: (_data, { uid }) => qc.invalidateQueries({ queryKey: ["events", uid] }),
  });
}

export function useRemoveEventPlace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (uid: string) => api.removeEventPlace(uid),
    onSuccess: (_data, uid) => qc.invalidateQueries({ queryKey: ["events", uid] }),
  });
}
