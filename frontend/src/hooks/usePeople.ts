import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "../api/people";
import type { PersonCreate, PersonUpdate } from "../types/people";

export function usePeople() {
  return useQuery({ queryKey: ["people"], queryFn: api.listPeople });
}

export function usePerson(uid: string) {
  return useQuery({ queryKey: ["people", uid], queryFn: () => api.getPerson(uid) });
}

export function useCreatePerson() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (person: PersonCreate) => api.createPerson(person),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["people"] }),
  });
}

export function useUpdatePerson() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ uid, updates }: { uid: string; updates: PersonUpdate }) =>
      api.updatePerson(uid, updates),
    onSuccess: (_data, { uid }) => {
      qc.invalidateQueries({ queryKey: ["people"] });
      qc.invalidateQueries({ queryKey: ["people", uid] });
    },
  });
}

export function usePersonEvents(uid: string) {
  return useQuery({ queryKey: ["people", uid, "events"], queryFn: () => api.getPersonEvents(uid) });
}

export function usePersonPlaces(uid: string) {
  return useQuery({ queryKey: ["people", uid, "places"], queryFn: () => api.getPersonPlaces(uid) });
}

export function useSetBornAt() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ uid, placeUid }: { uid: string; placeUid: string }) =>
      api.setBornAt(uid, placeUid),
    onSuccess: (_data, { uid }) => qc.invalidateQueries({ queryKey: ["people", uid] }),
  });
}

export function useRemoveBornAt() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (uid: string) => api.removeBornAt(uid),
    onSuccess: (_data, uid) => qc.invalidateQueries({ queryKey: ["people", uid] }),
  });
}

export function useAddAttended() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ uid, eventUid }: { uid: string; eventUid: string }) =>
      api.addAttended(uid, eventUid),
    onSuccess: (_data, { uid }) => qc.invalidateQueries({ queryKey: ["people", uid, "events"] }),
  });
}

export function useRemoveAttended() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ uid, eventUid }: { uid: string; eventUid: string }) =>
      api.removeAttended(uid, eventUid),
    onSuccess: (_data, { uid }) => qc.invalidateQueries({ queryKey: ["people", uid, "events"] }),
  });
}
