<script setup lang="ts">
import type { AdminRoomListItem } from "~~/shared/types/admin";
import { listAdminRooms } from "~/services/api/admin";

const toast = useToast();
const rooms = ref<AdminRoomListItem[]>([]);
const loading = ref(true);
const search = ref("");

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase();
  if (!q) return rooms.value;
  return rooms.value.filter(
    (r) =>
      r.room.name.toLowerCase().includes(q) ||
      r.owner.first_name.toLowerCase().includes(q) ||
      (r.owner.username ?? "").toLowerCase().includes(q),
  );
});

onMounted(async () => {
  try {
    rooms.value = await listAdminRooms();
  } catch {
    toast.add({ title: "Could not load rooms", color: "error" });
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="flex flex-col gap-4">
    <UInput
      v-model="search"
      icon="i-lucide-search"
      placeholder="Search by room or owner"
      class="max-w-sm"
    />

    <div v-if="loading" class="flex justify-center py-16">
      <UIcon
        name="i-lucide-loader-circle"
        class="text-muted size-6 animate-spin"
      />
    </div>

    <p v-else-if="filtered.length === 0" class="text-muted py-8 text-center text-sm">
      No rooms found.
    </p>

    <div v-else class="flex flex-col divide-y divide-default">
      <NuxtLink
        v-for="item in filtered"
        :key="item.room.id"
        :to="`/app/admin/rooms/${item.room.id}`"
        class="hover:bg-elevated/50 flex items-center gap-3 px-2 py-3 transition"
      >
        <UIcon name="i-lucide-users" class="text-primary size-5 shrink-0" />
        <div class="min-w-0 flex-1">
          <p class="text-highlighted truncate text-sm font-medium">
            {{ item.room.name }}
          </p>
          <p class="text-muted truncate text-xs">
            owner: {{ item.owner.first_name }}
            <template v-if="item.owner.username">
              (@{{ item.owner.username }})
            </template>
          </p>
        </div>
        <UBadge
          :label="`${item.member_count} member${item.member_count === 1 ? '' : 's'}`"
          variant="subtle"
          size="sm"
        />
        <span class="text-muted text-xs tabular-nums">
          {{ new Date(item.room.created_at).toLocaleDateString() }}
        </span>
        <UIcon name="i-lucide-chevron-right" class="text-muted size-4" />
      </NuxtLink>
    </div>
  </div>
</template>
