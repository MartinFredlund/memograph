import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "../api/images";
import type { ImageUpdate, ImageListParams, ImageCountParams, PersonTagCreate } from "../types/images";

export function useImages(params: ImageListParams = {}) {
  return useQuery({
    queryKey: ["images", params],
    queryFn: () => api.listImages(params),
  });
}

export function useImage(uid: string) {
  return useQuery({
    queryKey: ["images", uid],
    queryFn: () => api.getImage(uid),
  });
}

export function useImageCount(params: ImageCountParams = {}) {
  return useQuery({
    queryKey: ["images", "count", params],
    queryFn: () => api.getImageCount(params),
  });
}

export function useUploadImages() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (files: File[]) => api.uploadImages(files),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["images"] });
    },
  });
}

export function useUpdateImage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ uid, updates }: { uid: string; updates: ImageUpdate }) =>
      api.updateImage(uid, updates),
    onSuccess: (_data, { uid }) => {
      qc.invalidateQueries({ queryKey: ["images"] });
      qc.invalidateQueries({ queryKey: ["images", uid] });
    },
  });
}

export function useDeleteImage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (uid: string) => api.deleteImage(uid),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["images"] }),
  });
}

export function useRotateImage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ uid, degrees }: { uid: string; degrees: 90 | 180 | 270 }) =>
      api.rotateImage(uid, degrees),
    onSuccess: (_data, { uid }) => {
      qc.invalidateQueries({ queryKey: ["images"] });
      qc.invalidateQueries({ queryKey: ["images", uid] });
    },
  });
}

export function useAddTag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ uid, tag }: { uid: string; tag: PersonTagCreate }) =>
      api.addTag(uid, tag),
    onSuccess: (_data, { uid }) => {
      qc.invalidateQueries({ queryKey: ["images", uid] });
      qc.invalidateQueries({ queryKey: ["images"] });
    },
  });
}

export function useRemoveTag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ uid, personUid }: { uid: string; personUid: string }) =>
      api.removeTag(uid, personUid),
    onSuccess: (_data, { uid }) => {
      qc.invalidateQueries({ queryKey: ["images", uid] });
      qc.invalidateQueries({ queryKey: ["images"] });
    },
  });
}

export function useSetImagePlace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ uid, placeUid }: { uid: string; placeUid: string }) =>
      api.setImagePlace(uid, placeUid),
    onSuccess: (_data, { uid }) => qc.invalidateQueries({ queryKey: ["images", uid] }),
  });
}

export function useRemoveImagePlace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (uid: string) => api.removeImagePlace(uid),
    onSuccess: (_data, uid) => qc.invalidateQueries({ queryKey: ["images", uid] }),
  });
}

export function useSetImageEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ uid, eventUid }: { uid: string; eventUid: string }) =>
      api.setImageEvent(uid, eventUid),
    onSuccess: (_data, { uid }) => qc.invalidateQueries({ queryKey: ["images", uid] }),
  });
}

export function useRemoveImageEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (uid: string) => api.removeImageEvent(uid),
    onSuccess: (_data, uid) => qc.invalidateQueries({ queryKey: ["images", uid] }),
  });
}
