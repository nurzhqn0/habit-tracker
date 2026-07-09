<script setup lang="ts">
import type { RoomHabitWithLink } from "~~/shared/types/rooms";
import { paletteColor } from "~/composables/usePalette";

const store = useRoomStore();
const toast = useToast();

const formOpen = ref(false);
const editing = ref<RoomHabitWithLink | null>(null);
const linkPickerFor = ref<RoomHabitWithLink | null>(null);
const deleteFor = ref<RoomHabitWithLink | null>(null);

function openHabitForm(item?: RoomHabitWithLink) {
  editing.value = item ?? null;
  formOpen.value = true;
}

async function unlink(item: RoomHabitWithLink) {
  await store.unlink(item.habit.id);
}

async function deleteHabit() {
  if (!deleteFor.value) return;
  try {
    await store.deleteHabit(deleteFor.value.habit.id);
    deleteFor.value = null;
  } catch {
    toast.add({ title: "Could not delete room habit", color: "error" });
  }
}
</script>

<template>
  <div class="flex flex-col gap-3 pt-4">
    <div v-if="store.isAdmin" class="flex justify-end">
      <UButton
        icon="i-lucide-plus"
        label="Add room habit"
        size="sm"
        @click="openHabitForm()"
      />
    </div>

    <p
      v-if="store.habits.length === 0"
      class="text-muted py-10 text-center text-sm"
    >
      No room habits yet.{{
        store.isAdmin ? " Add one so members can link their habits." : ""
      }}
    </p>

    <UCard v-for="item in store.habits" :key="item.habit.id">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-3">
          <span
            class="size-3 shrink-0 rounded-full"
            :style="{ backgroundColor: paletteColor(item.habit.color) }"
          />
          <div>
            <p class="text-highlighted font-medium">
              {{ item.habit.name }}
            </p>
            <p class="text-muted text-xs">
              {{ item.members_linked }} member{{
                item.members_linked === 1 ? "" : "s"
              }}
              linked
              <template v-if="item.habit.type === 1">
                ·
                {{ item.habit.target_type === 0 ? "at least" : "at most" }}
                {{ item.habit.target_value }} {{ item.habit.unit }}
              </template>
            </p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <template v-if="item.linked_habit_id">
            <UButton
              :to="`/app/habits/${item.linked_habit_id}`"
              size="sm"
              variant="subtle"
              icon="i-lucide-chart-line"
              label="My habit"
            />
            <UButton
              size="sm"
              color="neutral"
              variant="ghost"
              icon="i-lucide-unlink"
              aria-label="Unlink"
              @click="unlink(item)"
            />
          </template>
          <UButton
            v-else
            size="sm"
            icon="i-lucide-link"
            label="Link my habit"
            @click="
              () => {
                linkPickerFor = item;
              }
            "
          />
          <template v-if="store.isAdmin">
            <UButton
              size="sm"
              color="neutral"
              variant="ghost"
              icon="i-lucide-pencil"
              aria-label="Edit room habit"
              @click="openHabitForm(item)"
            />
            <UButton
              size="sm"
              color="error"
              variant="ghost"
              icon="i-lucide-trash-2"
              aria-label="Delete room habit"
              @click="
                () => {
                  deleteFor = item;
                }
              "
            />
          </template>
        </div>
      </div>
    </UCard>

    <RoomsHabitModal v-model:open="formOpen" :item="editing" />
    <RoomsLinkPickerModal v-model="linkPickerFor" />
    <ConfirmModal
      :open="!!deleteFor"
      :title="`Delete “${deleteFor?.habit.name}”?`"
      description="Members' personal habits are kept, but unlinked from this room."
      confirm-label="Delete habit"
      confirm-icon="i-lucide-trash-2"
      @update:open="deleteFor = null"
      @confirm="deleteHabit"
    />
  </div>
</template>
