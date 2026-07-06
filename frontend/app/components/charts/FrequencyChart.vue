<script setup lang="ts">
const props = defineProps<{
  months: { month: string; weekdays: number[] }[];
  color: string;
  isNumerical?: boolean;
}>();

const LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const CELL = 26;

const max = computed(() => Math.max(1, ...props.months.flatMap((m) => m.weekdays)));

function radius(value: number): number {
  return value > 0 ? 2 + 7 * (value / max.value) : 0;
}

function displayValue(value: number): number {
  return props.isNumerical ? Math.round(value / 100) / 10 : value;
}

// Month short name; January shows the year instead (uhabits axis convention).
function monthLabel(month: string): string {
  const [y, m] = month.split("-").map(Number);
  if (m === 1) return String(y);
  return new Date(y!, m! - 1, 1).toLocaleDateString(undefined, { month: "short" });
}

const width = computed(() => props.months.length * CELL);
const HEIGHT = 7 * CELL;
</script>

<template>
  <p v-if="months.length === 0" class="text-sm text-muted">No entries yet.</p>
  <div v-else class="flex items-start gap-2">
    <div class="overflow-x-auto">
      <svg :width="width" :height="HEIGHT + 16" class="block">
        <g v-for="(m, ci) in months" :key="m.month">
          <circle
            v-for="(value, ri) in m.weekdays"
            :key="ri"
            :cx="ci * CELL + CELL / 2"
            :cy="ri * CELL + CELL / 2"
            :r="radius(value)"
            :fill="color"
          >
            <title>{{ m.month }} {{ LABELS[ri] }}: {{ displayValue(value) }}</title>
          </circle>
          <text
            :x="ci * CELL + CELL / 2"
            :y="HEIGHT + 12"
            text-anchor="middle"
            class="fill-[var(--ui-text-dimmed)] text-[9px]"
          >
            {{ monthLabel(m.month) }}
          </text>
        </g>
      </svg>
    </div>
    <div class="flex shrink-0 flex-col">
      <span
        v-for="label in LABELS"
        :key="label"
        class="flex items-center text-xs text-muted"
        :style="{ height: `${CELL}px` }"
      >
        {{ label }}
      </span>
    </div>
  </div>
</template>
