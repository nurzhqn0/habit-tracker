import { defineStore } from "pinia";
import type { EntryChange, Habit, HabitForm, HabitOverviewItem } from "~~/shared/types/habits";
import { apiFetch } from "~/services/api/client";

export type SortMode = "manual" | "name" | "color" | "score" | "status";

export const useHabitsStore = defineStore("habits", {
  state: () => ({
    items: [] as HabitOverviewItem[],
    loading: false,
    from: "",
    to: "",
    sort: "manual" as SortMode,
    showArchived: false,
  }),
  actions: {
    async loadOverview(from: string, to: string) {
      this.from = from;
      this.to = to;
      this.loading = this.items.length === 0;
      try {
        this.items = await apiFetch<HabitOverviewItem[]>("/habits/overview", {
          query: { from, to, sort: this.sort, include_archived: this.showArchived },
        });
      } finally {
        this.loading = false;
      }
    },

    async reload() {
      if (this.from && this.to) await this.loadOverview(this.from, this.to);
    },

    _applyChange(habitId: number, change: EntryChange) {
      const item = this.items.find((i) => i.habit.id === habitId);
      if (!item) return;
      item.score = change.score;
      item.streak = change.streak;
      const window: Record<string, number> = {};
      for (const [date, value] of Object.entries(change.entries)) {
        if (date >= this.from && date <= this.to) window[date] = value;
      }
      item.entries = window;
    },

    async toggle(habitId: number, date: string) {
      const item = this.items.find((i) => i.habit.id === habitId);
      const previous = item?.entries[date];
      if (item) item.entries[date] = previous === 2 ? 0 : 2; // optimistic guess
      try {
        const change = await apiFetch<EntryChange>(`/habits/${habitId}/entries/${date}/toggle`, {
          method: "POST",
        });
        this._applyChange(habitId, change);
      } catch (error) {
        if (item) {
          if (previous === undefined) delete item.entries[date];
          else item.entries[date] = previous;
        }
        throw error;
      }
    },

    async setValue(habitId: number, date: string, value: number, notes?: string) {
      const change = await apiFetch<EntryChange>(`/habits/${habitId}/entries/${date}`, {
        method: "PUT",
        body: { value, notes },
      });
      this._applyChange(habitId, change);
      const item = this.items.find((i) => i.habit.id === habitId);
      if (item && notes !== undefined) {
        if (notes) item.notes[date] = notes;
        else delete item.notes[date];
      }
    },

    async createHabit(form: HabitForm) {
      await apiFetch<Habit>("/habits", { method: "POST", body: form });
      await this.reload();
    },

    async updateHabit(habitId: number, form: Partial<HabitForm> & { clear_reminder?: boolean }) {
      await apiFetch<Habit>(`/habits/${habitId}`, { method: "PATCH", body: form });
      await this.reload();
    },

    async deleteHabit(habitId: number) {
      await apiFetch(`/habits/${habitId}`, { method: "DELETE" });
      this.items = this.items.filter((i) => i.habit.id !== habitId);
    },

    async setArchived(habitId: number, archived: boolean) {
      await apiFetch(`/habits/${habitId}/${archived ? "archive" : "unarchive"}`, { method: "POST" });
      await this.reload();
    },

    async reorder(orderedIds: number[]) {
      const order = new Map(orderedIds.map((id, index) => [id, index]));
      this.items.sort((a, b) => (order.get(a.habit.id) ?? 0) - (order.get(b.habit.id) ?? 0));
      await apiFetch("/habits/positions", { method: "PUT", body: { ordered_ids: orderedIds } });
    },
  },
});
