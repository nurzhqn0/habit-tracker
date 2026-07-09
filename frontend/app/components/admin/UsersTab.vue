<script setup lang="ts">
import type { AdminUser } from "~~/shared/types/admin";
import { listAdminUsers } from "~/services/api/admin";

const toast = useToast();
const users = ref<AdminUser[]>([]);
const loading = ref(true);
const search = ref("");

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase();
  if (!q) return users.value;
  return users.value.filter(
    (u) =>
      u.first_name.toLowerCase().includes(q) ||
      (u.username ?? "").toLowerCase().includes(q),
  );
});

onMounted(async () => {
  try {
    users.value = await listAdminUsers();
  } catch {
    toast.add({ title: "Could not load users", color: "error" });
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
      placeholder="Search by name or username"
      class="max-w-sm"
    />

    <div v-if="loading" class="flex justify-center py-16">
      <UIcon
        name="i-lucide-loader-circle"
        class="text-muted size-6 animate-spin"
      />
    </div>

    <p v-else-if="filtered.length === 0" class="text-muted py-8 text-center text-sm">
      No users found.
    </p>

    <div v-else class="flex flex-col divide-y divide-default">
      <NuxtLink
        v-for="user in filtered"
        :key="user.id"
        :to="`/app/admin/users/${user.id}`"
        class="hover:bg-elevated/50 flex items-center gap-3 px-2 py-3 transition"
      >
        <UAvatar
          :src="user.photo_url ?? undefined"
          :alt="user.first_name"
          size="sm"
        />
        <div class="min-w-0 flex-1">
          <p class="text-highlighted truncate text-sm font-medium">
            {{ user.first_name }}
          </p>
          <p class="text-muted truncate text-xs">
            <template v-if="user.username">@{{ user.username }}</template>
            <template v-else>no username</template>
          </p>
        </div>
        <UBadge v-if="user.bot_linked" label="bot" variant="subtle" size="sm" />
        <span class="text-muted text-xs tabular-nums">
          {{ new Date(user.created_at).toLocaleDateString() }}
        </span>
        <UIcon name="i-lucide-chevron-right" class="text-muted size-4" />
      </NuxtLink>
    </div>
  </div>
</template>
