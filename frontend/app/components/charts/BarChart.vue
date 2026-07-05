<script setup lang="ts">
const props = defineProps<{
  bars: { date: string; value: number }[];
  color: string;
  isNumerical: boolean;
  unit?: string;
}>();

const shown = computed(() => props.bars.slice(-24));
const max = computed(() => Math.max(1, ...shown.value.map((b) => b.value)));

function display(value: number): string {
  const real = props.isNumerical ? value / 1000 : value / 1000;
  return Number.isInteger(real) ? String(real) : real.toFixed(1);
}
</script>

<template>
  <div class="overflow-x-auto">
    <div class="flex h-40 min-w-fit items-end gap-1.5 pt-4">
      <div v-for="bar in shown" :key="bar.date" class="flex w-8 flex-col items-center gap-1">
        <span class="text-[9px] tabular-nums text-dimmed">{{ display(bar.value) }}</span>
        <div
          class="w-5 rounded-t-sm transition-all"
          :style="{ height: `${(bar.value / max) * 100}px`, backgroundColor: color }"
        />
        <span class="text-[9px] text-dimmed">{{ bar.date.slice(5) }}</span>
      </div>
    </div>
  </div>
</template>
