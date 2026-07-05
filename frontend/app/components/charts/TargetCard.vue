<script setup lang="ts">
defineProps<{
  rows: { period: string; actual: number; target: number }[];
  color: string;
  unit: string;
}>();

function width(actual: number, target: number): string {
  if (target <= 0) return actual > 0 ? "100%" : "0%";
  return `${Math.min(100, (actual / target) * 100)}%`;
}
</script>

<template>
  <div class="flex flex-col gap-2.5">
    <div v-for="row in rows" :key="row.period" class="flex items-center gap-3">
      <span class="w-16 text-xs capitalize text-muted">{{ row.period }}</span>
      <div class="h-4 flex-1 rounded-full bg-elevated">
        <div
          class="h-4 rounded-full transition-all"
          :style="{ width: width(row.actual, row.target), backgroundColor: color }"
        />
      </div>
      <span class="w-28 text-right text-xs tabular-nums text-muted">
        {{ Math.round(row.actual * 10) / 10 }} / {{ Math.round(row.target * 10) / 10 }} {{ unit }}
      </span>
    </div>
  </div>
</template>
