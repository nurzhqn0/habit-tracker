// Mirrors backend pydantic schemas (app/api/schemas).

export interface User {
  id: number;
  telegram_id: number;
  username: string | null;
  first_name: string;
  photo_url: string | null;
  bot_linked: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface Preferences {
  theme: "system" | "light" | "dark";
  show_question_marks: boolean;
  skip_days_enabled: boolean;
  first_weekday: number;
  timezone: string;
  reminders_enabled: boolean;
  room_notifications: boolean;
}

