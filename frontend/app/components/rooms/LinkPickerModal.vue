<script setup lang="ts">
import type { RoomHabitWithLink } from "~~/shared/types/rooms";
import type { Habit } from "~~/shared/types/habits";
import { listOwnHabits } from "~/services/api/rooms";
import { paletteColor } from "~/composables/usePalette";

const item = defineModel<RoomHabitWithLink | null>({ required: true });

const store = useRoomStore();
const toast = useToast();

const myHabits = ref<Habit[]>([]);
const busy = ref(false);

watch(item, async (value) => {
  if (!value) return;
  // Only same-type habits not already linked to a habit in this room.
  myHabits.value = [];
  const linkedIds = new Set(
    store.habits.map((h) => h.linked_habit_id).filter(Boolean),
  );
  myHabits.value = (await listOwnHabits()).filter(
    (h) => h.type === value.habit.type && !linkedIds.has(h.id),
  );
});

async function link(habitId: number | null) {
  if (!item.value) return;
  busy.value = true;
  try {
    await store.link(item.value.habit.id, habitId);
    item.value = null;
    toast.add({ title: "Habit linked", color: "success" });
  } catch (error: any) {
    const detail = error?.data?.detail ?? "Could not link habit";
    toast.add({ title: detail, color: "error" });
  } finally {
    busy.value = false;
  }
}

function linkTypeLabel(picked: RoomHabitWithLink): string {
  if (picked.habit.type !== 1) return "Yes / No";
  const direction = picked.habit.target_type === 0 ? "at least" : "at most";
  return `Measurable · ${direction} ${picked.habit.target_value} ${picked.habit.unit}`.trim();
}
</script>

<template>
  <UModal
    :open="!!item"
    :title="`Link a habit to “${item?.habit.name}”`"
    @update:open="item = null"
  >
    <template #body>
      <div class="flex flex-col gap-3">
        <UBadge v-if="item" variant="subtle" color="neutral" class="self-start">
          {{ linkTypeLabel(item) }}
        </UBadge>

        <UButton
          icon="i-lucide-plus"
          :label="`Create “${item?.habit.name}” from template`"
          variant="subtle"
          block
          :loading="busy"
          @click="link(null)"
        />

        <template v-if="myHabits.length">
          <p class="text-dimmed text-xs tracking-wide uppercase">
            or link an existing habit
          </p>
          <UButton
            v-for="habit in myHabits"
            :key="habit.id"
            color="neutral"
            variant="outline"
            block
            :loading="busy"
            @click="link(habit.id)"
          >
            <span
              class="size-2.5 shrink-0 rounded-full"
              :style="{ backgroundColor: paletteColor(habit.color) }"
            />
            <span class="truncate">{{ habit.name }}</span>
          </UButton>
        </template>
        <p v-else class="text-muted text-xs">
          No compatible habits to link — create one from the template above.
        </p>
      </div>
    </template>
  </UModal>
</template>
