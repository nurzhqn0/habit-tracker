<script setup lang="ts">
import type { Habit } from "~~/shared/types/habits";
import { apiFetch } from "~/services/api/client";
import { paletteColor } from "~/composables/usePalette";

definePageMeta({ layout: "dashboard" });

const route = useRoute();
const router = useRouter();
const toast = useToast();
const store = useHabitsStore();
const habitId = Number(route.params.id);

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
const editOpen = ref(false);

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
  scorePoints.value = await apiFetch(`/habits/${habitId}/stats/scores`, {
    query: { bucket: scoreBucket.value },
  });
}

async function loadBars() {
  bars.value = await apiFetch(`/habits/${habitId}/stats/bar`, {
    query: { bucket: barBucket.value },
  });
}

async function loadAll() {
  loading.value = true;
  try {
    habit.value = await apiFetch<Habit>(`/habits/${habitId}`);
    [overview.value, heatmap.value, weekdays.value, frequencyMonths.value, streaks.value, notes.value] =
      await Promise.all([
        apiFetch(`/habits/${habitId}/stats/overview`),
        apiFetch(`/habits/${habitId}/stats/history`),
        apiFetch(`/habits/${habitId}/stats/weekdays`),
        apiFetch(`/habits/${habitId}/stats/frequency`),
        apiFetch(`/habits/${habitId}/stats/streaks`),
        apiFetch(`/habits/${habitId}/stats/notes`),
        loadScores(),
        loadBars(),
      ]);
    if (habit.value?.type === 1) {
      targetRows.value = await apiFetch(`/habits/${habitId}/stats/target`);
    }
  } catch {
    toast.add({ title: "Could not load habit", color: "error" });
    router.replace("/app");
  } finally {
    loading.value = false;
  }
}

onMounted(loadAll);
watch(scoreBucket, loadScores);
watch(barBucket, loadBars);

const valueDate = ref<string | null>(null);
const valueInput = ref("");

async function onPickDay(date: string) {
  if (!habit.value) return;
  if (habit.value.type === 1) {
    const stored = heatmap.value?.entries?.[date];
    valueInput.value = stored !== undefined && stored >= 0 ? String(stored / 1000) : "";
    valueDate.value = date;
    return;
  }
  try {
    await apiFetch(`/habits/${habitId}/entries/${date}/toggle`, { method: "POST" });
    await loadAll();
  } catch {
    toast.add({ title: "Could not save entry", color: "error" });
  }
}

async function saveValue() {
  const date = valueDate.value;
  const parsed = Number(valueInput.value);
  if (!date || !Number.isFinite(parsed) || parsed < 0) return;
  valueDate.value = null;
  try {
    await apiFetch(`/habits/${habitId}/entries/${date}`, {
      method: "PUT",
      body: { value: Math.round(parsed * 1000) },
    });
    await loadAll();
  } catch {
    toast.add({ title: "Could not save entry", color: "error" });
  }
}

const deleteOpen = ref(false);

async function onDelete() {
  deleteOpen.value = false;
  await store.deleteHabit(habitId);
  toast.add({ title: `Deleted "${habit.value?.name}"` });
  router.replace("/app");
}

const BUCKETS = ["day", "week", "month", "quarter", "year"];
</script>

<template>
  <UDashboardPanel id="habit-detail">
    <template #header>
      <UDashboardNavbar :title="habit?.name ?? 'Habit'" :toggle="false">
        <template #leading>
          <UButton icon="i-lucide-arrow-left" color="neutral" variant="ghost" to="/app" aria-label="Back" />
        </template>
        <template #right>
          <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" label="Edit" @click="editOpen = true" />
          <UButton icon="i-lucide-trash-2" color="error" variant="ghost" aria-label="Delete" @click="deleteOpen = true" />
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
          <UBadge v-if="habit.reminder_hour !== null" variant="subtle" icon="i-lucide-bell">
            {{ String(habit.reminder_hour).padStart(2, "0") }}:{{ String(habit.reminder_min ?? 0).padStart(2, "0") }}
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
            <div class="flex items-center justify-between gap-2">
              <p class="font-semibold text-highlighted">History</p>
              <p class="text-xs text-muted">
                {{ habit.type === 1 ? "Tap a day to edit its value" : "Tap a day to toggle" }}
              </p>
            </div>
          </template>
          <ChartsHistoryHeatmap v-if="heatmap" :data="heatmap" :color="color" @pick="onPickDay" />
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

      <HabitFormModal v-model:open="editOpen" :habit="habit ?? undefined" @saved="loadAll" />

      <UModal
        :open="valueDate !== null"
        :title="valueDate ?? ''"
        description="Set the value for this day."
        @update:open="(open: boolean) => { if (!open) valueDate = null; }"
      >
        <template #body>
          <form class="flex items-center gap-2" @submit.prevent="saveValue">
            <UInput
              v-model="valueInput"
              type="number"
              step="any"
              min="0"
              autofocus
              :placeholder="`0 ${habit?.unit ?? ''}`"
              class="flex-1"
            />
            <span v-if="habit?.unit" class="text-xs text-muted">{{ habit.unit }}</span>
            <UButton type="submit" icon="i-lucide-check" label="Save" />
          </form>
        </template>
      </UModal>

      <UModal
        v-model:open="deleteOpen"
        :title="`Delete “${habit?.name}”?`"
        description="All its entries will be removed. This cannot be undone."
      >
        <template #footer>
          <div class="flex w-full justify-end gap-2">
            <UButton label="Cancel" color="neutral" variant="ghost" @click="deleteOpen = false" />
            <UButton label="Delete" color="error" icon="i-lucide-trash-2" @click="onDelete" />
          </div>
        </template>
      </UModal>
    </template>
  </UDashboardPanel>
</template>
