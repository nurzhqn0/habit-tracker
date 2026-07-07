import { defineStore } from "pinia";
import type { RoomMember } from "~~/shared/types/rooms";

/** In-memory navigation context for room pages: survives client-side
 *  navigation, intentionally resets on a full page reload. */
export const useRoomViewStore = defineStore("roomView", {
  state: () => ({
    activeTabs: {} as Record<number, string>,
    viewedMember: null as RoomMember | null,
    viewedHabit: null as { id: number; name: string } | null,
  }),
});
