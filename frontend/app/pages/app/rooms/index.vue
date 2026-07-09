<script setup lang="ts">
import type { Room } from "~~/shared/types/rooms";
import { apiFetch } from "~/services/api/client";

definePageMeta({ layout: "dashboard" });
useHead({ title: "Rooms" });

const toast = useToast();
const view = useRoomViewStore();
const rooms = ref<Room[]>([]);
const loading = ref(true);

function openRoom(room: Room) {
  view.viewedRoom = room;
  navigateTo(`/app/rooms/${room.id}`);
}

const createOpen = ref(false);
const joinOpen = ref(false);
const newRoom = reactive({ name: "", description: "" });
const joinCode = ref("");
const busy = ref(false);

async function load() {
  loading.value = true;
  try {
    rooms.value = await apiFetch<Room[]>("/rooms");
  } finally {
    loading.value = false;
  }
}

onMounted(load);

async function createRoom() {
  if (!newRoom.name.trim()) return;
  busy.value = true;
  try {
    const room = await apiFetch<Room>("/rooms", {
      method: "POST",
      body: { ...newRoom },
    });
    createOpen.value = false;
    newRoom.name = "";
    newRoom.description = "";
    openRoom(room);
  } catch {
    toast.add({ title: "Could not create room", color: "error" });
  } finally {
    busy.value = false;
  }
}

async function joinRoom() {
  if (!joinCode.value.trim()) return;
  busy.value = true;
  try {
    const room = await apiFetch<Room>("/rooms/join", {
      method: "POST",
      body: { code: joinCode.value.trim() },
    });
    joinOpen.value = false;
    joinCode.value = "";
    openRoom(room);
  } catch {
    toast.add({ title: "Invalid invite code", color: "error" });
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <UDashboardPanel id="rooms">
    <template #header>
      <UDashboardNavbar title="Rooms" :toggle="false">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #right>
          <UButton
            icon="i-lucide-log-in"
            label="Join"
            variant="subtle"
            @click="
              () => {
                joinOpen = true;
              }
            "
          />
          <UButton
            icon="i-lucide-plus"
            label="New room"
            @click="
              () => {
                createOpen = true;
              }
            "
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

      <div
        v-else-if="rooms.length === 0"
        class="mx-auto flex max-w-md flex-col items-center gap-4 py-20 text-center"
      >
        <UIcon name="i-lucide-users" class="text-muted size-10" />
        <p class="text-highlighted text-lg font-semibold">No rooms yet</p>
        <p class="text-muted text-sm">
          Rooms let you share habits with friends — everyone tracks their own
          progress and competes on the leaderboard.
        </p>
        <div class="flex gap-2">
          <UButton
            icon="i-lucide-plus"
            label="Create room"
            @click="
              () => {
                createOpen = true;
              }
            "
          />
          <UButton
            icon="i-lucide-log-in"
            label="Join with code"
            variant="subtle"
            @click="
              () => {
                joinOpen = true;
              }
            "
          />
        </div>
      </div>

      <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <NuxtLink
          v-for="room in rooms"
          :key="room.id"
          :to="`/app/rooms/${room.id}`"
          @click="view.viewedRoom = room"
        >
          <UCard
            class="hover:ring-primary h-28 overflow-hidden transition hover:ring-2 sm:h-32"
          >
            <div class="flex items-start gap-3">
              <UIcon
                name="i-lucide-users"
                class="text-primary mt-1 size-5 shrink-0"
              />
              <div class="min-w-0">
                <p class="text-highlighted truncate font-semibold">
                  {{ room.name }}
                </p>
                <p
                  v-if="room.description"
                  class="text-muted mt-1 line-clamp-2 text-sm whitespace-pre-line"
                >
                  {{ room.description }}
                </p>
              </div>
            </div>
          </UCard>
        </NuxtLink>
      </div>

      <UModal v-model:open="createOpen" title="Create room">
        <template #body>
          <form class="flex flex-col gap-4" @submit.prevent="createRoom">
            <UFormField label="Name" required>
              <UInput
                v-model="newRoom.name"
                placeholder="e.g. Morning Crew"
                class="w-full"
                autofocus
              />
            </UFormField>
            <UFormField label="Description">
              <UTextarea
                v-model="newRoom.description"
                :rows="2"
                class="w-full"
              />
            </UFormField>
          </form>
        </template>
        <template #footer>
          <div class="flex w-full justify-end gap-2">
            <UButton
              color="neutral"
              variant="ghost"
              label="Cancel"
              @click="
                () => {
                  createOpen = false;
                }
              "
            />
            <UButton
              :loading="busy"
              :disabled="!newRoom.name.trim()"
              label="Create"
              @click="createRoom"
            />
          </div>
        </template>
      </UModal>

      <UModal v-model:open="joinOpen" title="Join room">
        <template #body>
          <form class="flex flex-col gap-4" @submit.prevent="joinRoom">
            <UFormField label="Invite code" required>
              <UInput
                v-model="joinCode"
                placeholder="paste the code"
                class="w-full"
                autofocus
              />
            </UFormField>
          </form>
        </template>
        <template #footer>
          <div class="flex w-full justify-end gap-2">
            <UButton
              color="neutral"
              variant="ghost"
              label="Cancel"
              @click="
                () => {
                  joinOpen = false;
                }
              "
            />
            <UButton
              :loading="busy"
              :disabled="!joinCode.trim()"
              label="Join"
              @click="joinRoom"
            />
          </div>
        </template>
      </UModal>
    </template>
  </UDashboardPanel>
</template>
