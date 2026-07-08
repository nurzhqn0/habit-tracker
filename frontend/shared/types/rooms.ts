export interface Room {
  id: number;
  name: string;
  description: string;
  owner_id: number;
  invite_code: string;
  show_leaderboard: boolean;
  show_members: boolean;
  created_at: string;
}

export interface RoomMember {
  user_id: number;
  first_name: string;
  username: string | null;
  photo_url: string | null;
  role: "owner" | "admin" | "member";
  joined_at: string;
}

export interface RoomHabit {
  id: number;
  room_id: number;
  created_by: number;
  name: string;
  description: string;
  type: 0 | 1;
  color: number;
  freq_num: number;
  freq_den: number;
  target_type: 0 | 1;
  target_value: number;
  unit: string;
}

export interface RoomHabitWithLink {
  habit: RoomHabit;
  linked_habit_id: number | null;
  members_linked: number;
}

export interface LeaderboardRow {
  user_id: number;
  first_name: string;
  username: string | null;
  photo_url: string | null;
  score: number;
  streak: number;
  completions: number;
  linked_habits: number;
}

export interface FeedEvent {
  id: number;
  user_id: number;
  first_name: string;
  photo_url: string | null;
  type: string;
  room_habit_id: number | null;
  room_habit_name: string | null;
  entry_date: string | null;
  value: number | null;
  created_at: string;
}
