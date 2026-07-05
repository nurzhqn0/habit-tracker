<script setup lang="ts">
const props = defineProps<{
  weekdays: { weekday: number; value: number }[];
  color: string;
}>();

const LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const max = computed(() => Math.max(1, ...props.weekdays.map((w) => w.value)));
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <div v-for="w in weekdays" :key="w.weekday" class="flex items-center gap-2">
      <span class="w-9 text-xs text-muted">{{ LABELS[w.weekday] }}</span>
      <div class="h-4 flex-1 rounded bg-elevated">
        <div
          class="h-4 rounded transition-all"
          :style="{ width: `${(w.value / max) * 100}%`, backgroundColor: color }"
        />
      </div>
      <span class="w-10 text-right text-xs tabular-nums text-muted">{{ w.value }}</span>
    </div>
  </div>
</template>
