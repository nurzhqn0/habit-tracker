<script setup lang="ts">
import type { LeaderboardRow } from "~~/shared/types/rooms";
import { getLeaderboard } from "~/services/api/rooms";

const store = useRoomStore();
const auth = useAuthStore();

const period = ref<"week" | "month" | "all">("week");
const rows = ref<LeaderboardRow[]>([]);

async function load() {
  rows.value = await getLeaderboard(store.roomId, period.value);
}

onMounted(load);
watch(period, load);
</script>

<template>
  <div class="flex flex-col gap-3 pt-4">
    <div class="flex justify-end">
      <USelect
        v-model="period"
        :items="['week', 'month', 'all']"
        size="sm"
        class="w-28"
      />
    </div>
    <UCard>
      <ol class="divide-default flex flex-col divide-y">
        <li
          v-for="(row, index) in rows"
          :key="row.user_id"
          class="flex items-center gap-3 py-2.5"
        >
          <span
            class="w-6 text-center font-bold"
            :class="index === 0 ? 'text-warning' : 'text-muted'"
          >
            {{ index + 1 }}
          </span>
          <UAvatar
            :src="row.photo_url ?? undefined"
            :alt="row.first_name"
            size="sm"
          />
          <div class="min-w-0 flex-1">
            <p class="text-default truncate text-sm font-medium">
              {{ row.first_name }}
              <span
                v-if="row.user_id === auth.user?.id"
                class="text-muted text-xs"
                >(you)</span
              >
            </p>
            <p class="text-muted text-xs">
              {{ row.linked_habits }} linked habits
            </p>
          </div>
          <div class="flex items-center gap-4 text-sm tabular-nums">
            <span class="text-muted flex items-center gap-1">
              <UIcon name="i-lucide-flame" class="text-warning size-4" />{{
                row.streak
              }}
            </span>
            <span class="text-muted">{{ row.completions }} done</span>
            <span class="text-highlighted w-12 text-right font-semibold">
              {{ Math.round(row.score * 100) }}%
            </span>
          </div>
        </li>
      </ol>
    </UCard>
  </div>
</template>
