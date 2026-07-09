import { defineStore } from "pinia";
import type {
  Room,
  RoomHabitWithLink,
  RoomMember,
} from "~~/shared/types/rooms";
import type { RoomHabitForm, RoomSettingsForm } from "~/services/api/rooms";
import * as roomsApi from "~/services/api/rooms";

/** State of the room currently open at /app/rooms/:id, shared by the
 *  room page and its tab/modal components. */
export const useRoomStore = defineStore("room", {
  state: () => ({
    roomId: 0,
    room: null as Room | null,
    habits: [] as RoomHabitWithLink[],
    members: [] as RoomMember[],
    loading: true,
  }),
  getters: {
    isOwner(): boolean {
      return this.room?.owner_id === useAuthStore().user?.id;
    },
    myRole(): RoomMember["role"] | undefined {
      const userId = useAuthStore().user?.id;
      return this.members.find((m) => m.user_id === userId)?.role;
    },
    isAdmin(): boolean {
      return this.isOwner || this.myRole === "admin";
    },
  },
  actions: {
    async load(roomId: number) {
      const view = useRoomViewStore();
      this.roomId = roomId;
      // Seed from the room card the user tapped so the title shows instantly.
      this.room = view.viewedRoom?.id === roomId ? view.viewedRoom : null;
      this.habits = [];
      this.members = [];
      this.loading = true;
      try {
        this.room = await roomsApi.getRoom(roomId);
        await this.refresh();
      } finally {
        this.loading = false;
      }
    },

    async refresh() {
      [this.habits, this.members] = await Promise.all([
        roomsApi.listRoomHabits(this.roomId),
        roomsApi.listMembers(this.roomId),
      ]);
    },

    async saveHabit(form: RoomHabitForm, habitId: number | null) {
      if (habitId) {
        const { type, ...fields } = form;
        await roomsApi.updateRoomHabit(this.roomId, habitId, fields);
      } else {
        await roomsApi.createRoomHabit(this.roomId, form);
      }
      await this.refresh();
    },

    async deleteHabit(habitId: number) {
      await roomsApi.deleteRoomHabit(this.roomId, habitId);
      await this.refresh();
    },

    async link(roomHabitId: number, habitId: number | null) {
      await roomsApi.linkHabit(this.roomId, roomHabitId, habitId);
      await this.refresh();
    },

    async unlink(roomHabitId: number) {
      await roomsApi.unlinkHabit(this.roomId, roomHabitId);
      await this.refresh();
    },

    async removeMember(userId: number) {
      await roomsApi.removeMember(this.roomId, userId);
      // Leaving the room ourselves revokes access — skip the refetch.
      if (userId !== useAuthStore().user?.id) await this.refresh();
    },

    async setRole(userId: number, role: "admin" | "member") {
      await roomsApi.setMemberRole(this.roomId, userId, role);
      await this.refresh();
    },

    async transferOwnership(userId: number) {
      await roomsApi.transferOwnership(this.roomId, userId);
      this.room = await roomsApi.getRoom(this.roomId);
      await this.refresh();
    },

    async updateRoom(form: RoomSettingsForm) {
      this.room = await roomsApi.updateRoom(this.roomId, form);
    },

    async rotateInvite() {
      const result = await roomsApi.rotateInvite(this.roomId);
      if (this.room) this.room.invite_code = result.invite_code;
      return result.invite_code;
    },

    async deleteRoom() {
      await roomsApi.deleteRoom(this.roomId);
    },
  },
});
