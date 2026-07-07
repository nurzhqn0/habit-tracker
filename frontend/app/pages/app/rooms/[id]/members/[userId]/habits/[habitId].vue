<script setup lang="ts">
import type { Habit } from "~~/shared/types/habits";
import { apiFetch } from "~/services/api/client";
import { paletteColor } from "~/composables/usePalette";

definePageMeta({ layout: "dashboard" });

const route = useRoute();
const router = useRouter();
const toast = useToast();
const roomId = Number(route.params.id);
const userId = Number(route.params.userId);
const habitId = Number(route.params.habitId);
const base = `/rooms/${roomId}/members/${userId}/habits/${habitId}`;
const backTo = `/app/rooms/${roomId}/members/${userId}`;

const habit = ref<Habit | null>(null);
const overview = ref<any>(null);
const scorePoints = ref<{ date: string; value: number }[]>([]);
const heatmap = ref<any>(null);
const bars = ref<{ date: string; value: number }[]>([]);
const weekdays = ref<{ weekday: number; value: number }[]>([]);
const frequencyMonths = ref<{ month: string; weekdays: number[] }[]>([]);
const streaks = ref<{ start: string; end: string; length: number }[]>([]);
const targetRows = ref<{ period: string; actual: number; target: number }[]>([]);
const notes = ref<{ date: string; value: number; notes: string }[]>([]);

const scoreBucket = ref<"day" | "week" | "month" | "quarter" | "year">("day");
const barBucket = ref<"week" | "month" | "quarter" | "year">("week");
const loading = ref(true);

const color = computed(() => paletteColor(habit.value?.color ?? 8));

useHead({ title: computed(() => habit.value?.name ?? "Habit") });

const frequencyLabel = computed(() => {
  if (!habit.value) return "";
  const { freq_num: num, freq_den: den } = habit.value;
  if (num === 1 && den === 1) return "Every day";
  if (num === 1 && den === 7) return "Every week";
  if (den === 7) return `${num} times per week`;
  if (num === 1 && (den === 30 || den === 31)) return "Every month";
  return `${num} times per ${den} days`;
});

async function loadScores() {
  scorePoints.value = await apiFetch(`${base}/stats/scores`, {
    query: { bucket: scoreBucket.value },
  });
}

async function loadBars() {
  bars.value = await apiFetch(`${base}/stats/bar`, {
    query: { bucket: barBucket.value },
  });
}

async function loadAll() {
  loading.value = true;
  try {
    habit.value = await apiFetch<Habit>(base);
    [overview.value, heatmap.value, weekdays.value, frequencyMonths.value, streaks.value, notes.value] =
      await Promise.all([
        apiFetch(`${base}/stats/overview`),
        apiFetch(`${base}/stats/history`),
        apiFetch(`${base}/stats/weekdays`),
        apiFetch(`${base}/stats/frequency`),
        apiFetch(`${base}/stats/streaks`),
        apiFetch(`${base}/stats/notes`),
        loadScores(),
        loadBars(),
      ]);
    if (habit.value?.type === 1) {
      targetRows.value = await apiFetch(`${base}/stats/target`);
    }
  } catch {
    toast.add({ title: "Could not load habit", color: "error" });
    router.replace(backTo);
  } finally {
    loading.value = false;
  }
}

onMounted(loadAll);
watch(scoreBucket, loadScores);
watch(barBucket, loadBars);

const BUCKETS = ["day", "week", "month", "quarter", "year"];
</script>

<template>
  <UDashboardPanel id="member-habit-detail">
    <template #header>
      <UDashboardNavbar :title="habit?.name ?? 'Habit'" :toggle="false">
        <template #leading>
          <UButton icon="i-lucide-arrow-left" color="neutral" variant="ghost" :to="backTo" aria-label="Back" />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div v-if="loading" class="flex justify-center py-16">
        <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin text-muted" />
      </div>

      <div v-else-if="habit" class="mx-auto flex w-full max-w-4xl flex-col gap-4">
        <div class="flex flex-wrap items-center gap-2 text-sm text-muted">
          <UBadge :style="{ backgroundColor: color }" class="text-white">{{ frequencyLabel }}</UBadge>
          <UBadge v-if="habit.type === 1" variant="subtle">
            {{ habit.target_type === 0 ? "At least" : "At most" }} {{ habit.target_value }} {{ habit.unit }}
          </UBadge>
          <span v-if="habit.question" class="italic">“{{ habit.question }}”</span>
        </div>

        <ChartsOverviewCard v-if="overview" :stats="overview" :color="color" />

        <UCard>
          <template #header>
            <div class="flex items-center justify-between">
              <p class="font-semibold text-highlighted">Score</p>
              <USelect v-model="scoreBucket" :items="BUCKETS" size="sm" class="w-28" />
            </div>
          </template>
          <ChartsScoreChart :points="scorePoints" :color="color" />
        </UCard>

        <UCard>
          <template #header>
            <p class="font-semibold text-highlighted">History</p>
          </template>
          <ChartsHistoryHeatmap v-if="heatmap" :data="heatmap" :color="color" />
        </UCard>

        <div class="grid gap-4 lg:grid-cols-2">
          <UCard>
            <template #header>
              <div class="flex items-center justify-between">
                <p class="font-semibold text-highlighted">{{ habit.type === 1 ? "Totals" : "Completions" }}</p>
                <USelect v-model="barBucket" :items="BUCKETS.slice(1)" size="sm" class="w-28" />
              </div>
            </template>
            <ChartsBarChart :bars="bars" :color="color" :is-numerical="habit.type === 1" :unit="habit.unit" />
          </UCard>

          <UCard>
            <template #header>
              <p class="font-semibold text-highlighted">Best days</p>
            </template>
            <ChartsWeekdayChart :weekdays="weekdays" :color="color" />
          </UCard>
        </div>

        <UCard>
          <template #header>
            <p class="font-semibold text-highlighted">Frequency</p>
          </template>
          <ChartsFrequencyChart
            :months="frequencyMonths"
            :color="color"
            :is-numerical="habit.type === 1"
          />
        </UCard>

        <UCard v-if="habit.type === 1">
          <template #header>
            <p class="font-semibold text-highlighted">Target</p>
          </template>
          <ChartsTargetCard :rows="targetRows" :color="color" :unit="habit.unit" />
        </UCard>

        <UCard>
          <template #header>
            <p class="font-semibold text-highlighted">Best streaks</p>
          </template>
          <ChartsStreakChart :streaks="streaks" :color="color" />
        </UCard>

        <UCard v-if="notes.length">
          <template #header>
            <p class="font-semibold text-highlighted">Notes</p>
          </template>
          <ul class="flex flex-col gap-2">
            <li v-for="note in notes" :key="note.date" class="flex gap-3 text-sm">
              <span class="shrink-0 tabular-nums text-dimmed">{{ note.date }}</span>
              <span class="text-default">{{ note.notes }}</span>
            </li>
          </ul>
        </UCard>

        <p v-if="habit.description" class="px-1 text-sm text-muted">{{ habit.description }}</p>
      </div>
    </template>
  </UDashboardPanel>
</template>
