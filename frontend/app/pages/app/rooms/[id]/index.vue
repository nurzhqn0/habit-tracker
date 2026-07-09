<script setup lang="ts">
definePageMeta({ layout: "dashboard" });

const route = useRoute();
const router = useRouter();
const toast = useToast();
const store = useRoomStore();
const view = useRoomViewStore();
const roomId = Number(route.params.id);

const tabs = computed(() => [
  {
    label: "Habits",
    slot: "habits",
    value: "habits",
    icon: "i-lucide-list-checks",
  },
  ...(store.isAdmin || store.room?.show_leaderboard
    ? [
        {
          label: "Leaderboard",
          slot: "leaderboard",
          value: "leaderboard",
          icon: "i-lucide-trophy",
        },
      ]
    : []),
  ...(store.isAdmin
    ? [
        {
          label: "Feed",
          slot: "feed",
          value: "feed",
          icon: "i-lucide-activity",
        },
      ]
    : []),
  ...(store.isAdmin || store.room?.show_members
    ? [
        {
          label: "Members",
          slot: "members",
          value: "members",
          icon: "i-lucide-users",
        },
      ]
    : []),
]);

const tab = computed({
  get: () => {
    const active = view.activeTabs[roomId] ?? "habits";
    return tabs.value.some((t) => t.value === active) ? active : "habits";
  },
  set: (value: string) => {
    view.activeTabs[roomId] = value;
  },
});

useHead({ title: computed(() => store.room?.name ?? "Room") });

const inviteOpen = ref(false);
const settingsOpen = ref(false);
const deleteRoomOpen = ref(false);

onMounted(async () => {
  try {
    await store.load(roomId);
  } catch {
    toast.add({ title: "Room not found", color: "error" });
    router.replace("/app/rooms");
  }
});

async function deleteRoom() {
  deleteRoomOpen.value = false;
  await store.deleteRoom();
  router.replace("/app/rooms");
}
</script>

<template>
  <UDashboardPanel id="room-detail">
    <template #header>
      <UDashboardNavbar :toggle="false">
        <template #leading>
          <UButton
            icon="i-lucide-arrow-left"
            color="neutral"
            variant="ghost"
            to="/app/rooms"
            aria-label="Back"
          />
        </template>
        <template #title>
          <span v-if="store.room">{{ store.room.name }}</span>
          <USkeleton v-else class="h-5 w-32" />
        </template>
        <template #right>
          <ExportMenu
            v-if="store.isAdmin"
            :path="`/rooms/${roomId}/export/xlsx`"
          />
          <UButton
            v-if="store.isAdmin"
            icon="i-lucide-user-plus"
            label="Invite"
            variant="subtle"
            @click="
              () => {
                inviteOpen = true;
              }
            "
          />
          <UButton
            v-if="store.isAdmin"
            icon="i-lucide-settings"
            color="neutral"
            variant="ghost"
            aria-label="Room settings"
            @click="
              () => {
                settingsOpen = true;
              }
            "
          />
          <UButton
            v-if="store.isOwner"
            icon="i-lucide-trash-2"
            color="error"
            variant="ghost"
            aria-label="Delete room"
            @click="
              () => {
                deleteRoomOpen = true;
              }
            "
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

      <UTabs
        v-else
        v-model="tab"
        :items="tabs"
        class="w-full"
        variant="link"
        :ui="{
          list: 'overflow-x-auto overflow-y-hidden',
          trigger: 'flex-none',
        }"
      >
        <template #habits>
          <RoomsHabitsTab />
        </template>
        <template #leaderboard>
          <RoomsLeaderboardTab />
        </template>
        <template #feed>
          <RoomsFeedTab />
        </template>
        <template #members>
          <RoomsMembersTab />
        </template>
      </UTabs>

      <RoomsInviteModal v-model:open="inviteOpen" />
      <RoomsSettingsModal v-model:open="settingsOpen" />
      <ConfirmModal
        v-model:open="deleteRoomOpen"
        :title="`Delete “${store.room?.name}”?`"
        description="The room, its habits and feed will be removed for every member. This cannot be undone."
        confirm-label="Delete room"
        confirm-icon="i-lucide-trash-2"
        @confirm="deleteRoom"
      />
    </template>
  </UDashboardPanel>
</template>
