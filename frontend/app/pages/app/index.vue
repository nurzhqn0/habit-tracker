<script setup lang="ts">
import draggable from "vuedraggable";
import type { DropdownMenuItem } from "@nuxt/ui";
import type { Habit, HabitOverviewItem } from "~~/shared/types/habits";
import { apiFetch } from "~/services/api/client";
import type { Preferences } from "~~/shared/types/api";
import {
  lastNDateKeys,
  todayKey,
  weekdayShort,
  dayOfMonth,
} from "~/composables/useDates";
import { paletteColor } from "~/composables/usePalette";

definePageMeta({ layout: "dashboard" });
useHead({ title: "Habits" });

const store = useHabitsStore();
const toast = useToast();

const prefs = ref<Preferences | null>(null);
const period = ref<"week" | "month">("week");
const periodItems = [
  { label: "Week", value: "week" },
  { label: "Month", value: "month" },
];
const dayCount = computed(() => (period.value === "week" ? 7 : 31));
const days = computed(() => lastNDateKeys(dayCount.value)); // newest first
const today = todayKey();

const formOpen = ref(false);
const editing = ref<Habit | undefined>();
const deleting = ref<Habit | null>(null);

async function confirmDelete() {
  const habit = deleting.value;
  if (!habit) return;
  deleting.value = null;
  try {
    await store.deleteHabit(habit.id);
  } catch {
    toast.add({ title: "Could not delete habit", color: "error" });
  }
}

async function load() {
  const range = days.value;
  await store.loadOverview(range[range.length - 1]!, range[0]!);
}

onMounted(async () => {
  prefs.value = await apiFetch<Preferences>("/me/preferences").catch(
    () => null,
  );
  await load().catch(() =>
    toast.add({ title: "Could not load habits", color: "error" }),
  );
});

watch(period, () => {
  load().catch(() =>
    toast.add({ title: "Could not load habits", color: "error" }),
  );
});

const sortItems = computed<DropdownMenuItem[]>(() =>
  (
    [
      ["manual", "Manual order", "i-lucide-grip-vertical"],
      ["name", "By name", "i-lucide-arrow-down-a-z"],
      ["color", "By color", "i-lucide-palette"],
      ["score", "By strength", "i-lucide-trending-up"],
      ["status", "By today's status", "i-lucide-circle-check"],
    ] as const
  ).map(([value, label, icon]) => ({
    label,
    icon,
    type: "checkbox" as const,
    checked: store.sort === value,
    onSelect: async () => {
      store.sort = value;
      await load();
    },
  })),
);

async function onToggle(item: HabitOverviewItem, date: string) {
  try {
    await store.toggle(item.habit.id, date);
  } catch {
    toast.add({ title: "Could not save entry", color: "error" });
  }
}

async function onSetValue(
  item: HabitOverviewItem,
  date: string,
  value: number,
) {
  try {
    await store.setValue(item.habit.id, date, value);
  } catch {
    toast.add({ title: "Could not save entry", color: "error" });
  }
}

function openCreate() {
  formOpen.value = true;
  editing.value = undefined;
}

function openEdit(habit: Habit) {
  editing.value = habit;
  formOpen.value = true;
}

function rowMenu(item: HabitOverviewItem): DropdownMenuItem[][] {
  const habit = item.habit;
  return [
    [
      {
        label: "Details",
        icon: "i-lucide-chart-line",
        to: `/app/habits/${habit.id}`,
      },
      {
        label: "Edit",
        icon: "i-lucide-pencil",
        onSelect: () => openEdit(habit),
      },
    ],
    [
      {
        label: "Delete",
        icon: "i-lucide-trash-2",
        color: "error",
        onSelect: () => {
          deleting.value = habit;
        },
      },
    ],
  ];
}

const dragEnabled = computed(() => store.sort === "manual");

async function onDragEnd() {
  await store.reorder(store.items.map((i) => i.habit.id)).catch(() => {
    toast.add({ title: "Could not reorder", color: "error" });
    load();
  });
}
</script>

<template>
  <UDashboardPanel id="habits">
    <template #header>
      <UDashboardNavbar title="Habits" :toggle="false">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #right>
          <USelect
            v-model="period"
            :items="periodItems"
            size="sm"
            class="w-24"
            aria-label="Period"
          />
          <ExportMenu path="/export/report/xlsx" />
          <UDropdownMenu :items="sortItems">
            <UButton
              icon="i-lucide-arrow-up-down"
              color="neutral"
              variant="ghost"
              aria-label="Sort"
            />
          </UDropdownMenu>
          <UButton
            icon="i-lucide-plus"
            label="New habit"
            class="hidden sm:inline-flex"
            @click="openCreate"
          />
          <UButton
            icon="i-lucide-plus"
            aria-label="New habit"
            class="sm:hidden"
            @click="openCreate"
          />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div v-if="store.loading" class="flex justify-center py-16">
        <UIcon
          name="i-lucide-loader-circle"
          class="text-muted size-6 animate-spin"
        />
      </div>

      <div
        v-else-if="store.items.length === 0"
        class="mx-auto flex max-w-md flex-col items-center gap-4 py-20 text-center"
      >
        <UIcon name="i-lucide-sprout" class="text-muted size-10" />
        <p class="text-highlighted text-lg font-semibold">No habits yet</p>
        <p class="text-muted text-sm">
          Create your first habit and start building streaks.
        </p>
        <UButton
          icon="i-lucide-plus"
          label="Create habit"
          @click="openCreate"
        />
      </div>

      <div v-else class="min-w-fit">
        <div>
          <div class="border-default flex items-center gap-2 border-b pb-2">
            <div
              class="bg-default sticky left-0 z-10 flex flex-1 items-center gap-2 self-stretch"
            >
              <div class="w-6 shrink-0" />
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
            <div class="w-8 shrink-0" />
          </div>

          <draggable
            v-model="store.items"
            item-key="habit.id"
            handle=".drag-handle"
            :disabled="!dragEnabled"
            @end="onDragEnd"
          >
            <template #item="{ element: item }">
              <div
                data-testid="habit-row"
                class="border-default flex items-center gap-2 border-b py-1"
              >
                <div
                  class="bg-default sticky left-0 z-10 flex flex-1 items-center gap-2 self-stretch"
                >
                  <UIcon
                    name="i-lucide-grip-vertical"
                    class="drag-handle text-dimmed w-6 shrink-0"
                    :class="dragEnabled ? 'cursor-grab' : 'opacity-20'"
                  />

                  <NuxtLink
                    :to="`/app/habits/${item.habit.id}`"
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
                    @save="(value) => onSetValue(item, date, value)"
                  />
                  <HabitCheckmarkCell
                    v-else
                    :value="item.entries[date]"
                    :color="paletteColor(item.habit.color)"
                    :show-question-marks="prefs?.show_question_marks ?? false"
                    @toggle="onToggle(item, date)"
                  />
                </template>

                <UDropdownMenu :items="rowMenu(item)">
                  <UButton
                    icon="i-lucide-ellipsis-vertical"
                    color="neutral"
                    variant="ghost"
                    size="sm"
                    class="w-8 shrink-0"
                    aria-label="Habit menu"
                  />
                </UDropdownMenu>
              </div>
            </template>
          </draggable>
        </div>
      </div>

      <HabitFormModal v-model:open="formOpen" :habit="editing" />

      <UModal
        :open="deleting !== null"
        :title="`Delete “${deleting?.name}”?`"
        description="All its entries will be removed. This cannot be undone."
        @update:open="
          (open: boolean) => {
            if (!open) deleting = null;
          }
        "
      >
        <template #footer>
          <div class="flex w-full justify-end gap-2">
            <UButton
              label="Cancel"
              color="neutral"
              variant="ghost"
              @click="
                () => {
                  deleting = null;
                }
              "
            />
            <UButton
              label="Delete"
              color="error"
              icon="i-lucide-trash-2"
              @click="confirmDelete"
            />
          </div>
        </template>
      </UModal>
    </template>
  </UDashboardPanel>
</template>
