import type {
  FeedEvent,
  LeaderboardRow,
  Room,
  RoomHabitWithLink,
  RoomMember,
} from "~~/shared/types/rooms";
import type { Habit } from "~~/shared/types/habits";
import { apiFetch } from "~/services/api/client";

export interface RoomHabitForm {
  name: string;
  type: 0 | 1;
  target_value: number;
  unit: string;
  freq_num: number;
  freq_den: number;
}

export interface RoomSettingsForm {
  name: string;
  description: string;
  show_leaderboard: boolean;
  show_members: boolean;
}

export interface InviteResult {
  status: "sent" | "not_linked" | "not_registered" | "already_member";
  username: string;
  link: string;
}

export function getRoom(roomId: number) {
  return apiFetch<Room>(`/rooms/${roomId}`);
}

export function updateRoom(roomId: number, form: RoomSettingsForm) {
  return apiFetch<Room>(`/rooms/${roomId}`, { method: "PATCH", body: form });
}

export function deleteRoom(roomId: number) {
  return apiFetch(`/rooms/${roomId}`, { method: "DELETE" });
}

export function listRoomHabits(roomId: number) {
  return apiFetch<RoomHabitWithLink[]>(`/rooms/${roomId}/habits`);
}

export function createRoomHabit(roomId: number, form: RoomHabitForm) {
  return apiFetch(`/rooms/${roomId}/habits`, { method: "POST", body: form });
}

export function updateRoomHabit(
  roomId: number,
  habitId: number,
  form: Omit<RoomHabitForm, "type">,
) {
  return apiFetch(`/rooms/${roomId}/habits/${habitId}`, {
    method: "PATCH",
    body: form,
  });
}

export function deleteRoomHabit(roomId: number, habitId: number) {
  return apiFetch(`/rooms/${roomId}/habits/${habitId}`, { method: "DELETE" });
}

export function linkHabit(
  roomId: number,
  roomHabitId: number,
  habitId: number | null,
) {
  return apiFetch(`/rooms/${roomId}/habits/${roomHabitId}/link`, {
    method: "POST",
    body: habitId ? { habit_id: habitId } : {},
  });
}

export function unlinkHabit(roomId: number, roomHabitId: number) {
  return apiFetch(`/rooms/${roomId}/habits/${roomHabitId}/link`, {
    method: "DELETE",
  });
}

export function listMembers(roomId: number) {
  return apiFetch<RoomMember[]>(`/rooms/${roomId}/members`);
}

export function removeMember(roomId: number, userId: number) {
  return apiFetch(`/rooms/${roomId}/members/${userId}`, { method: "DELETE" });
}

export function setMemberRole(
  roomId: number,
  userId: number,
  role: "admin" | "member",
) {
  return apiFetch(`/rooms/${roomId}/members/${userId}`, {
    method: "PATCH",
    body: { role },
  });
}

export function transferOwnership(roomId: number, userId: number) {
  return apiFetch(`/rooms/${roomId}/transfer-ownership`, {
    method: "POST",
    body: { user_id: userId },
  });
}

export function getLeaderboard(
  roomId: number,
  period: "week" | "month" | "all",
) {
  return apiFetch<LeaderboardRow[]>(`/rooms/${roomId}/leaderboard`, {
    query: { period },
  });
}

export function getFeed(
  roomId: number,
  options: { limit: number; cursor?: number },
) {
  return apiFetch<FeedEvent[]>(`/rooms/${roomId}/feed`, {
    query: {
      limit: options.limit,
      ...(options.cursor ? { cursor: options.cursor } : {}),
    },
  });
}

export function sendInvite(roomId: number, username: string) {
  return apiFetch<InviteResult>(`/rooms/${roomId}/invite`, {
    method: "POST",
    body: { username },
  });
}

export function rotateInvite(roomId: number) {
  return apiFetch<{ invite_code: string }>(`/rooms/${roomId}/invite/rotate`, {
    method: "POST",
  });
}

/** Personal habits, used by the link picker. */
export function listOwnHabits() {
  return apiFetch<Habit[]>("/habits");
}
