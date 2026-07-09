import type {
  AdminRoomDetail,
  AdminRoomListItem,
  AdminStats,
  AdminUser,
  AdminUserDetail,
} from "~~/shared/types/admin";
import { apiFetch } from "~/services/api/client";

export function getAdminStats() {
  return apiFetch<AdminStats>("/admin/stats");
}

export function listAdminUsers() {
  return apiFetch<AdminUser[]>("/admin/users");
}

export function getAdminUser(userId: number, from: string, to: string) {
  return apiFetch<AdminUserDetail>(`/admin/users/${userId}`, {
    query: { from, to },
  });
}

export function listAdminRooms() {
  return apiFetch<AdminRoomListItem[]>("/admin/rooms");
}

export function getAdminRoom(roomId: number) {
  return apiFetch<AdminRoomDetail>(`/admin/rooms/${roomId}`);
}
