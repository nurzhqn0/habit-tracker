<script setup lang="ts">
import { NO, SKIP, YES_AUTO, YES_MANUAL } from "~~/shared/types/habits";
import { shiftDateKey } from "~/composables/useDates";

const props = defineProps<{
  data: {
    today: string;
    first_weekday: number;
    target_value: number;
    target_type: number;
    type: number;
    entries: Record<string, number>;
  };
  color: string;
  weeks?: number;
}>();

const emit = defineEmits<{ pick: [date: string] }>();

const weekCount = computed(() => props.weeks ?? 26);

// Grid: one column per week, rows Mon..Sun (respecting first_weekday), ending at today.
const columns = computed(() => {
  const { today, first_weekday } = props.data;
  const todayDate = new Date(today);
  const weekdayIndex = (todayDate.getDay() + 6) % 7; // Mon=0
  const offsetToWeekEnd = ((first_weekday + 6) % 7) - weekdayIndex; // days until last cell of current week
  const lastCell = shiftDateKey(today, ((offsetToWeekEnd % 7) + 7) % 7);

  const result: { date: string; future: boolean }[][] = [];
  for (let w = weekCount.value - 1; w >= 0; w--) {
    const column: { date: string; future: boolean }[] = [];
    for (let d = 6; d >= 0; d--) {
      const date = shiftDateKey(lastCell, -(w * 7 + d));
      column.push({ date, future: date > today });
    }
    result.push(column);
  }
  return result;
});

function cellStyle(date: string, future: boolean): Record<string, string> {
  if (future) return { backgroundColor: "transparent" };
  const value = props.data.entries[date];
  const base = { backgroundColor: "var(--ui-bg-elevated)" };
  if (value === undefined) return base;

  if (props.data.type === 1) {
    if (value === SKIP || value < 0) return base;
    const target = props.data.target_value * 1000;
    const ratio = target > 0 ? Math.min(1, value / target) : value > 0 ? 1 : 0;
    const strength = props.data.target_type === 1 ? (value <= target ? 1 : 0.25) : ratio;
    if (strength <= 0) return base;
    return { backgroundColor: props.color, opacity: String(0.25 + 0.75 * strength) };
  }

  switch (value) {
    case YES_MANUAL:
      return { backgroundColor: props.color };
    case YES_AUTO:
      return { backgroundColor: props.color, opacity: "0.45" };
    case SKIP:
      return { backgroundColor: props.color, opacity: "0.25" };
    case NO:
    default:
      return base;
  }
}

const monthLabels = computed(() => {
  const labels: { index: number; label: string }[] = [];
  let last = "";
  columns.value.forEach((column, index) => {
    const month = column[0]!.date.slice(0, 7);
    if (month !== last) {
      labels.push({ index, label: column[0]!.date.slice(5, 7) });
      last = month;
    }
  });
  return labels.slice(1); // skip partial first label
});
</script>

<template>
  <div class="overflow-x-auto">
    <div class="min-w-fit">
      <div class="relative mb-1 h-3">
        <span
          v-for="m in monthLabels"
          :key="m.index"
          class="absolute text-[9px] text-dimmed"
          :style="{ left: `${m.index * 14}px` }"
        >
          {{ m.label }}
        </span>
      </div>
      <div class="flex gap-[3px]">
        <div v-for="(column, ci) in columns" :key="ci" class="flex flex-col gap-[3px]">
          <button
            v-for="cell in column"
            :key="cell.date"
            type="button"
            class="size-[11px] rounded-[3px] transition hover:ring-1 hover:ring-[var(--ui-border-accented)]"
            :style="cellStyle(cell.date, cell.future)"
            :title="cell.date"
            :disabled="cell.future"
            @click="emit('pick', cell.date)"
          />
        </div>
      </div>
    </div>
  </div>
</template>
