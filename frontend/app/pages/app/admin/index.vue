<script setup lang="ts">
import type { AdminStats } from "~~/shared/types/admin";
import { getAdminStats } from "~/services/api/admin";

definePageMeta({ layout: "dashboard", middleware: "admin" });
useHead({ title: "Admin" });

const toast = useToast();
const stats = ref<AdminStats | null>(null);

const tabs = [
  { label: "Users", icon: "i-lucide-user", slot: "users" as const },
  { label: "Rooms", icon: "i-lucide-users", slot: "rooms" as const },
];

onMounted(async () => {
  try {
    stats.value = await getAdminStats();
  } catch {
    toast.add({ title: "Could not load stats", color: "error" });
  }
});
</script>

<template>
  <UDashboardPanel id="admin">
    <template #header>
      <UDashboardNavbar title="Admin" :toggle="false">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="flex flex-col gap-6">
        <div class="grid grid-cols-3 gap-4">
          <AdminStatCard
            label="Users"
            :value="stats?.total_users ?? null"
            icon="i-lucide-user"
          />
          <AdminStatCard
            label="Rooms"
            :value="stats?.total_rooms ?? null"
            icon="i-lucide-users"
          />
          <AdminStatCard
            label="Habits"
            :value="stats?.total_habits ?? null"
            icon="i-lucide-list-checks"
          />
        </div>

        <UTabs :items="tabs" variant="link">
          <template #users>
            <AdminUsersTab class="pt-4" />
          </template>
          <template #rooms>
            <AdminRoomsTab class="pt-4" />
          </template>
        </UTabs>
      </div>
    </template>
  </UDashboardPanel>
</template>
