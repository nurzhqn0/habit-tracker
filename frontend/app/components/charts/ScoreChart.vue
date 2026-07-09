<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  points: { date: string; value: number }[];
  color: string;
}>();

const W = 640;
const H = 160;
const PAD = { top: 10, right: 8, bottom: 22, left: 34 };

const path = computed(() => {
  const pts = props.points;
  if (pts.length === 0) return "";
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;
  const step = pts.length > 1 ? innerW / (pts.length - 1) : 0;
  return pts
    .map((p, i) => {
      const x = PAD.left + i * step;
      const y = PAD.top + innerH * (1 - Math.min(1, Math.max(0, p.value)));
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
});

const gridLines = [0, 0.25, 0.5, 0.75, 1];

function yFor(value: number): number {
  return PAD.top + (H - PAD.top - PAD.bottom) * (1 - value);
}

const xLabels = computed(() => {
  const pts = props.points;
  if (pts.length === 0) return [];
  const count = Math.min(6, pts.length);
  const innerW = W - PAD.left - PAD.right;
  return Array.from({ length: count }, (_, i) => {
    const index = Math.round((i / Math.max(1, count - 1)) * (pts.length - 1));
    return {
      x: PAD.left + (pts.length > 1 ? (index / (pts.length - 1)) * innerW : 0),
      label: pts[index]!.date.slice(5),
    };
  });
});
</script>

<template>
  <div class="overflow-x-auto">
    <svg :viewBox="`0 0 ${W} ${H}`" class="min-w-96 w-full">
      <g v-for="line in gridLines" :key="line">
        <line
          :x1="PAD.left" :x2="W - PAD.right" :y1="yFor(line)" :y2="yFor(line)"
          class="stroke-[var(--ui-border)]" stroke-width="1"
        />
        <text
          :x="PAD.left - 6" :y="yFor(line) + 3"
          text-anchor="end" class="fill-[var(--ui-text-dimmed)] text-[9px]"
        >
          {{ Math.round(line * 100) }}%
        </text>
      </g>
      <path :d="path" fill="none" :stroke="color" stroke-width="2" stroke-linejoin="round" />
      <text
        v-for="label in xLabels" :key="label.x"
        :x="label.x" :y="H - 6" text-anchor="middle"
        class="fill-[var(--ui-text-dimmed)] text-[9px]"
      >
        {{ label.label }}
      </text>
    </svg>
  </div>
</template>
