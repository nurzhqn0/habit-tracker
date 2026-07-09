<script setup lang="ts">
import type { AdminUserDetail } from "~~/shared/types/admin";
import { getAdminUser } from "~/services/api/admin";
import {
  lastNDateKeys,
  todayKey,
  weekdayShort,
  dayOfMonth,
} from "~/composables/useDates";
import { paletteColor } from "~/composables/usePalette";

definePageMeta({ layout: "dashboard", middleware: "admin" });

const route = useRoute();
const router = useRouter();
const toast = useToast();
const userId = Number(route.params.userId);

const detail = ref<AdminUserDetail | null>(null);
const loading = ref(true);

const period = ref<"week" | "month">("week");
const periodItems = [
  { label: "Week", value: "week" },
  { label: "Month", value: "month" },
];
const dayCount = computed(() => (period.value === "week" ? 7 : 31));
const days = computed(() => lastNDateKeys(dayCount.value)); // newest first
const today = todayKey();

const title = computed(() =>
  detail.value ? `${detail.value.user.first_name} — habits` : "User habits",
);
useHead({ title });

async function load() {
  const range = days.value;
  detail.value = await getAdminUser(userId, range[range.length - 1]!, range[0]!);
}

onMounted(async () => {
  try {
    await load();
  } catch {
    toast.add({ title: "Could not load user", color: "error" });
    router.replace("/app/admin");
    return;
  }
  loading.value = false;
});

watch(period, () => {
  load().catch(() =>
    toast.add({ title: "Could not load habits", color: "error" }),
  );
});
</script>

<template>
  <UDashboardPanel id="admin-user">
    <template #header>
      <UDashboardNavbar :toggle="false">
        <template #leading>
          <UButton
            icon="i-lucide-arrow-left"
            color="neutral"
            variant="ghost"
            to="/app/admin"
            aria-label="Back"
          />
        </template>
        <template #title>
          <span v-if="detail">{{ detail.user.first_name }} — habits</span>
          <USkeleton v-else class="h-5 w-36" />
        </template>
        <template #right>
          <UAvatar
            v-if="detail"
            :src="detail.user.photo_url ?? undefined"
            :alt="detail.user.first_name"
            size="sm"
          />
          <USkeleton v-else class="size-7 rounded-full" />
          <USelect
            v-model="period"
            :items="periodItems"
            size="sm"
            class="w-24"
            aria-label="Period"
          />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div v-if="loading" class="flex justify-center py-16">
        <UIcon
          name="i-lucide-loader-circle"
          class="text-muted size-6 animate-spin"
        />
      </div>

      <div v-else-if="detail" class="flex flex-col gap-6">
        <UCard>
          <div class="flex items-center gap-4">
            <UAvatar
              :src="detail.user.photo_url ?? undefined"
              :alt="detail.user.first_name"
              size="lg"
            />
            <div class="min-w-0 flex-1">
              <p class="text-highlighted truncate font-semibold">
                {{ detail.user.first_name }}
              </p>
              <p class="text-muted truncate text-sm">
                <template v-if="detail.user.username">
                  @{{ detail.user.username }}
                </template>
                <template v-else>no username</template>
                · id {{ detail.user.telegram_id }}
              </p>
            </div>
            <div class="text-muted text-right text-xs">
              <p>
                joined
                {{ new Date(detail.user.created_at).toLocaleDateString() }}
              </p>
              <UBadge
                v-if="detail.user.bot_linked"
                label="bot linked"
                variant="subtle"
                size="sm"
              />
            </div>
          </div>
        </UCard>

        <div
          v-if="detail.habits.length === 0"
          class="mx-auto flex max-w-md flex-col items-center gap-4 py-12 text-center"
        >
          <UIcon name="i-lucide-sprout" class="text-muted size-10" />
          <p class="text-highlighted text-lg font-semibold">No habits yet</p>
        </div>

        <div v-else class="min-w-fit">
          <div class="border-default flex items-center gap-2 border-b pb-2">
            <div
              class="bg-default sticky left-0 z-10 flex flex-1 items-center gap-2 self-stretch"
            >
              <div class="min-w-28 flex-1 sm:min-w-40" />
            </div>
            <div
              v-for="date in days"
              :key="date"
              class="text-muted w-9 text-center text-[10px] leading-tight uppercase"
            >
              <div>{{ weekdayShort(date) }}</div>
              <div
                class="font-semibold"
                :class="date === today ? 'text-primary' : ''"
              >
                {{ dayOfMonth(date) }}
              </div>
            </div>
          </div>

          <div
            v-for="item in detail.habits"
            :key="item.habit.id"
            class="border-default flex items-center gap-2 border-b py-1"
          >
            <div
              class="bg-default sticky left-0 z-10 flex flex-1 items-center gap-2 self-stretch"
            >
              <NuxtLink
                :to="`/app/admin/users/${userId}/habits/${item.habit.id}`"
                class="flex min-w-28 flex-1 items-center gap-3 sm:min-w-40"
              >
                <HabitScoreRing
                  :score="item.score"
                  :color="paletteColor(item.habit.color)"
                />
                <div class="min-w-0">
                  <p
                    class="truncate text-sm font-medium"
                    :style="{ color: paletteColor(item.habit.color) }"
                  >
                    {{ item.habit.name }}
                  </p>
                  <p
                    v-if="item.streak > 1"
                    class="text-muted flex items-center gap-1 text-xs"
                  >
                    <UIcon name="i-lucide-flame" class="size-3" />{{
                      item.streak
                    }}
                    days
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
                :show-question-marks="false"
                readonly
              />
            </template>
          </div>
        </div>
      </div>
    </template>
  </UDashboardPanel>
</template>
