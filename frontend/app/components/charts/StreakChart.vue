<script setup lang="ts">
const props = defineProps<{
  streaks: { start: string; end: string; length: number }[];
  color: string;
}>();

const max = computed(() => Math.max(1, ...props.streaks.map((s) => s.length)));
</script>

<template>
  <div v-if="streaks.length === 0" class="py-6 text-center text-sm text-muted">
    No streaks yet — complete a day to start one.
  </div>
  <div v-else class="flex flex-col gap-1.5">
    <div v-for="s in streaks" :key="s.end" class="flex items-center gap-2 text-xs">
      <span class="w-20 text-right tabular-nums text-dimmed">{{ s.start }}</span>
      <div class="flex flex-1 justify-center">
        <div
          class="flex h-5 min-w-8 items-center justify-center rounded-full text-[10px] font-bold text-white"
          :style="{ width: `${(s.length / max) * 100}%`, backgroundColor: color, opacity: 0.5 + 0.5 * (s.length / max) }"
        >
          {{ s.length }}
        </div>
      </div>
      <span class="w-20 tabular-nums text-dimmed">{{ s.end }}</span>
    </div>
  </div>
</template>
