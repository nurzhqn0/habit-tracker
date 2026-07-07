<script setup lang="ts">
import { SKIP, YES_AUTO, YES_MANUAL } from "~~/shared/types/habits";
import { shiftDateKey, weekdayShort, dayOfMonth } from "~/composables/useDates";

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

const CELL = 28; // px, matches size-7
const GAP = 4; // px, matches gap-1
const COL = CELL + GAP;

// Grid: one column per week, rows ordered by first_weekday, ending at today.
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

const weekdayLabels = computed(() => columns.value[0]?.map((c) => weekdayShort(c.date)) ?? []);

function cellStyle(date: string, future: boolean): Record<string, string> {
  if (future) return { backgroundColor: "transparent" };
  const halo =
    date === props.data.today
      ? { boxShadow: `0 0 0 1px var(--ui-bg), 0 0 0 3px ${props.color}` }
      : {};
  const value = props.data.entries[date];
  const empty = { backgroundColor: "var(--ui-bg-elevated)", color: "var(--ui-text-dimmed)", ...halo };
  if (value === undefined) return empty;

  if (props.data.type === 1) {
    if (value === SKIP || value < 0) return empty;
    const target = props.data.target_value * 1000;
    const ratio = target > 0 ? Math.min(1, value / target) : value > 0 ? 1 : 0;
    const strength = props.data.target_type === 1 ? (value <= target ? 1 : 0.25) : ratio;
    if (strength <= 0) return empty;
    return {
      backgroundColor: `color-mix(in srgb, ${props.color} ${Math.round(25 + 75 * strength)}%, transparent)`,
      color: strength >= 0.5 ? "white" : props.color,
      ...halo,
    };
  }

  switch (value) {
    case YES_MANUAL:
      return { backgroundColor: props.color, color: "white", ...halo };
    case YES_AUTO:
      return {
        backgroundColor: `color-mix(in srgb, ${props.color} 45%, transparent)`,
        color: "white",
        ...halo,
      };
    case SKIP:
      return {
        backgroundColor: `color-mix(in srgb, ${props.color} 18%, transparent)`,
        color: props.color,
        ...halo,
      };
    default:
      return empty;
  }
}

const MONTH_GAP = 12; // px, extra space dividing columns that start a new month

// Column indices where a new month begins — they get the divider gap.
const monthStarts = computed(() => {
  const starts = new Set<number>();
  let last = "";
  columns.value.forEach((column, index) => {
    const month = column[0]!.date.slice(0, 7);
    if (index > 0 && month !== last) starts.add(index);
    last = month;
  });
  return starts;
});

// Left edge of each column in px, accounting for the month divider gaps.
const columnOffsets = computed(() => {
  const offsets: number[] = [];
  let x = 0;
  columns.value.forEach((_, index) => {
    if (monthStarts.value.has(index)) x += MONTH_GAP;
    offsets.push(x);
    x += COL;
  });
  return offsets;
});

const monthLabels = computed(() => {
  const labels: { index: number; label: string }[] = [];
  let last = "";
  columns.value.forEach((column, index) => {
    const month = column[0]!.date.slice(0, 7);
    if (month !== last) {
      const [y, m] = month.split("-").map(Number);
      const name = new Date(y!, m! - 1, 1).toLocaleDateString(undefined, { month: "short" });
      labels.push({ index, label: m === 1 ? `${name} ${y}` : name });
      last = month;
    }
  });
  return labels.slice(1); // skip partial first label
});

// Newest data is at the right edge — start scrolled to it on narrow screens.
const scroller = ref<HTMLElement | null>(null);
onMounted(() => {
  if (scroller.value) scroller.value.scrollLeft = scroller.value.scrollWidth;
});
</script>

<template>
  <div class="flex items-start gap-2">
    <div ref="scroller" class="overflow-x-auto pb-1">
      <div class="min-w-fit">
        <div class="relative mb-1.5 h-4">
          <span
            v-for="m in monthLabels"
            :key="m.index"
            class="absolute text-[10px] font-medium whitespace-nowrap text-muted"
            :style="{ left: `${columnOffsets[m.index]}px` }"
          >
            {{ m.label }}
          </span>
        </div>
        <div class="flex gap-1">
          <div
            v-for="(column, ci) in columns"
            :key="ci"
            class="flex flex-col gap-1"
            :style="monthStarts.has(ci) ? { marginLeft: `${MONTH_GAP}px` } : undefined"
          >
            <button
              v-for="cell in column"
              :key="cell.date"
              type="button"
              class="flex size-7 items-center justify-center rounded-md text-[10px] font-medium tabular-nums transition hover:ring-2 hover:ring-[var(--ui-border-accented)] active:scale-90 disabled:cursor-default"
              :style="cellStyle(cell.date, cell.future)"
              :title="cell.date"
              :disabled="cell.future"
              :aria-label="cell.date"
              @click="emit('pick', cell.date)"
            >
              {{ cell.future ? "" : dayOfMonth(cell.date) }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="mt-[22px] flex shrink-0 flex-col gap-1">
      <span
        v-for="(label, i) in weekdayLabels"
        :key="i"
        class="flex h-7 items-center text-[10px] text-muted"
      >
        {{ label }}
      </span>
    </div>
  </div>
</template>
