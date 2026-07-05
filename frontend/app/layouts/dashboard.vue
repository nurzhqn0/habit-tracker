<script setup lang="ts">
import type { NavigationMenuItem } from "@nuxt/ui";

const auth = useAuthStore();

const items = computed<NavigationMenuItem[]>(() => [
  { label: "Habits", icon: "i-lucide-list-checks", to: "/app" },
  { label: "Rooms", icon: "i-lucide-users", to: "/app/rooms" },
  { label: "Settings", icon: "i-lucide-settings", to: "/app/settings" },
]);
</script>

<template>
  <UDashboardGroup>
    <UDashboardSidebar collapsible :min-size="14" :default-size="16">
      <template #header="{ collapsed }">
        <NuxtLink to="/app" class="flex items-center gap-2 font-bold text-highlighted">
          <UIcon name="i-lucide-activity" class="size-5 text-primary" />
          <span v-if="!collapsed">HabitFlow</span>
        </NuxtLink>
      </template>

      <template #default="{ collapsed }">
        <UNavigationMenu :collapsed="collapsed" :items="items" orientation="vertical" />
      </template>

      <template #footer="{ collapsed }">
        <div class="flex w-full items-center gap-2" :class="collapsed ? 'flex-col' : ''">
          <UAvatar :src="auth.user?.photo_url ?? undefined" :alt="auth.user?.first_name" size="sm" />
          <span v-if="!collapsed" class="flex-1 truncate text-sm text-muted">
            {{ auth.user?.first_name }}
          </span>
          <UColorModeButton />
          <UTooltip text="Logout">
            <UButton
              icon="i-lucide-log-out"
              color="neutral"
              variant="ghost"
              aria-label="Logout"
              @click="auth.logout()"
            />
          </UTooltip>
        </div>
      </template>
    </UDashboardSidebar>

    <slot />
  </UDashboardGroup>
</template>
