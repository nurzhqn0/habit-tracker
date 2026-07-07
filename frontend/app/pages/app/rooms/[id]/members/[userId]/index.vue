<script setup lang="ts">
import type { HabitOverviewItem } from "~~/shared/types/habits";
import type { RoomMember } from "~~/shared/types/rooms";
import { apiFetch } from "~/services/api/client";
import type { Preferences } from "~~/shared/types/api";
import { lastNDateKeys, todayKey, weekdayShort, dayOfMonth } from "~/composables/useDates";
import { paletteColor } from "~/composables/usePalette";

definePageMeta({ layout: "dashboard" });

const route = useRoute();
const router = useRouter();
const toast = useToast();
const roomId = Number(route.params.id);
const userId = Number(route.params.userId);

const items = ref<HabitOverviewItem[]>([]);
const member = ref<RoomMember | null>(null);
const prefs = ref<Preferences | null>(null);
const loading = ref(true);

const period = ref<"week" | "month">("week");
const periodItems = [
  { label: "Week", value: "week" },
  { label: "Month", value: "month" },
];
const dayCount = computed(() => (period.value === "week" ? 7 : 31));
const days = computed(() => lastNDateKeys(dayCount.value)); // newest first
const today = todayKey();

const title = computed(() => (member.value ? `${member.value.first_name} — habits` : "Member habits"));
useHead({ title });

async function load() {
  const range = days.value;
  items.value = await apiFetch<HabitOverviewItem[]>(`/rooms/${roomId}/members/${userId}/overview`, {
    query: { from: range[range.length - 1], to: range[0] },
  });
}

onMounted(async () => {
  prefs.value = await apiFetch<Preferences>("/me/preferences").catch(() => null);
  try {
    const members = await apiFetch<RoomMember[]>(`/rooms/${roomId}/members`);
    member.value = members.find((m) => m.user_id === userId) ?? null;
    await load();
  } catch {
    toast.add({ title: "Could not load member habits", color: "error" });
    router.replace(`/app/rooms/${roomId}`);
    return;
  }
  loading.value = false;
});

watch(period, () => {
  load().catch(() => toast.add({ title: "Could not load habits", color: "error" }));
});
</script>

<template>
  <UDashboardPanel id="member-habits">
    <template #header>
      <UDashboardNavbar :title="title" :toggle="false">
        <template #leading>
          <UButton
            icon="i-lucide-arrow-left"
            color="neutral"
            variant="ghost"
            :to="`/app/rooms/${roomId}`"
            aria-label="Back"
          />
        </template>
        <template #right>
          <UAvatar
            v-if="member"
            :src="member.photo_url ?? undefined"
            :alt="member.first_name"
            size="sm"
          />
          <USelect v-model="period" :items="periodItems" size="sm" class="w-24" aria-label="Period" />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div v-if="loading" class="flex justify-center py-16">
        <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin text-muted" />
      </div>

      <div
        v-else-if="items.length === 0"
        class="mx-auto flex max-w-md flex-col items-center gap-4 py-20 text-center"
      >
        <UIcon name="i-lucide-sprout" class="size-10 text-muted" />
        <p class="text-lg font-semibold text-highlighted">No habits linked to this room</p>
        <p class="text-sm text-muted">
          {{ member?.first_name ?? "This member" }} hasn't linked any habits here yet.
        </p>
      </div>

      <div v-else class="overflow-x-auto">
        <div class="min-w-fit">
          <div class="flex items-center gap-2 border-b border-default pb-2">
            <div class="sticky left-0 z-10 flex flex-1 items-center gap-2 self-stretch bg-default">
              <div class="min-w-28 flex-1 sm:min-w-40" />
            </div>
            <div
              v-for="date in days"
              :key="date"
              class="w-9 text-center text-[10px] uppercase leading-tight text-muted"
            >
              <div>{{ weekdayShort(date) }}</div>
              <div class="font-semibold" :class="date === today ? 'text-primary' : ''">
                {{ dayOfMonth(date) }}
              </div>
            </div>
          </div>

          <div
            v-for="item in items"
            :key="item.habit.id"
            data-testid="member-habit-row"
            class="flex items-center gap-2 border-b border-default py-1"
            :class="item.habit.archived ? 'opacity-50' : ''"
          >
            <div class="sticky left-0 z-10 flex flex-1 items-center gap-2 self-stretch bg-default">
              <NuxtLink
                :to="`/app/rooms/${roomId}/members/${userId}/habits/${item.habit.id}`"
                class="flex min-w-28 flex-1 items-center gap-3 sm:min-w-40"
              >
                <HabitScoreRing :score="item.score" :color="paletteColor(item.habit.color)" />
                <div class="min-w-0">
                  <p
                    class="truncate text-sm font-medium"
                    :style="{ color: paletteColor(item.habit.color) }"
                  >
                    {{ item.habit.name }}
                  </p>
                  <p v-if="item.streak > 1" class="flex items-center gap-1 text-xs text-muted">
                    <UIcon name="i-lucide-flame" class="size-3" />{{ item.streak }} days
                  </p>
                </div>
              </NuxtLink>
            </div>

            <template v-for="date in days" :key="date">
              <HabitNumberCell
                v-if="item.habit.type === 1"
                :value="item.entries[date]"
                :target-value="item.habit.target_value"
                :target-type="item.habit.target_type"
                :color="paletteColor(item.habit.color)"
                :unit="item.habit.unit"
                readonly
              />
              <HabitCheckmarkCell
                v-else
                :value="item.entries[date]"
                :color="paletteColor(item.habit.color)"
                :show-question-marks="prefs?.show_question_marks ?? false"
                readonly
              />
            </template>
          </div>
        </div>
      </div>
    </template>
  </UDashboardPanel>
</template>
