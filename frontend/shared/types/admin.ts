import type { HabitOverviewItem } from "./habits";
import type { Room, RoomHabit, RoomMember } from "./rooms";

export interface AdminStats {
  total_users: number;
  total_rooms: number;
  total_habits: number;
}

export interface AdminUser {
  id: number;
  telegram_id: number;
  username: string | null;
  first_name: string;
  photo_url: string | null;
  bot_linked: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface AdminUserDetail {
  user: AdminUser;
  habits: HabitOverviewItem[];
}

export interface AdminRoomListItem {
  room: Room;
  owner: AdminUser;
  member_count: number;
}

export interface AdminRoomDetail {
  room: Room;
  owner: AdminUser;
  members: RoomMember[];
  habits: RoomHabit[];
}
