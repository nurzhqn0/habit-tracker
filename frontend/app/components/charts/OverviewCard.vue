<script setup lang="ts">
defineProps<{
  stats: {
    score_today: number;
    score_month_diff: number;
    score_year_diff: number;
    total_count: number;
    streak: number;
  };
  color: string;
}>();

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function diff(value: number): string {
  const rounded = Math.round(value * 100);
  return `${rounded >= 0 ? "+" : ""}${rounded}%`;
}
</script>

<template>
  <UCard>
    <div class="grid grid-cols-2 gap-4 sm:grid-cols-5">
      <div class="flex items-center gap-3 sm:col-span-1">
        <HabitScoreRing :score="stats.score_today" :color="color" :size="52" />
        <div>
          <p class="text-2xl font-bold tabular-nums" :style="{ color }">{{ pct(stats.score_today) }}</p>
          <p class="text-xs text-muted">strength</p>
        </div>
      </div>
      <div>
        <p class="text-lg font-semibold tabular-nums" :class="stats.score_month_diff >= 0 ? 'text-success' : 'text-error'">
          {{ diff(stats.score_month_diff) }}
        </p>
        <p class="text-xs text-muted">vs last month</p>
      </div>
      <div>
        <p class="text-lg font-semibold tabular-nums" :class="stats.score_year_diff >= 0 ? 'text-success' : 'text-error'">
          {{ diff(stats.score_year_diff) }}
        </p>
        <p class="text-xs text-muted">vs last year</p>
      </div>
      <div>
        <p class="text-lg font-semibold tabular-nums text-highlighted">{{ stats.total_count }}</p>
        <p class="text-xs text-muted">total done</p>
      </div>
      <div>
        <p class="flex items-center gap-1 text-lg font-semibold tabular-nums text-highlighted">
          <UIcon name="i-lucide-flame" class="size-4 text-warning" />{{ stats.streak }}
        </p>
        <p class="text-xs text-muted">current streak</p>
      </div>
    </div>
  </UCard>
</template>
