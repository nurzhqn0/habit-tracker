<script setup lang="ts">
import type { NavigationMenuItem } from "@nuxt/ui";

const auth = useAuthStore();
const route = useRoute();

const items = computed<NavigationMenuItem[]>(() => [
  { label: "Habits", icon: "i-lucide-list-checks", to: "/app" },
  { label: "Rooms", icon: "i-lucide-users", to: "/app/rooms" },
  { label: "Settings", icon: "i-lucide-settings", to: "/app/settings" },
]);

function isActive(to: string): boolean {
  return to === "/app" ? route.path === "/app" : route.path.startsWith(to);
}
</script>

<template>
  <UDashboardGroup>
    <UDashboardSidebar collapsible :min-size="14" :default-size="18">
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
          <UTooltip v-if="!collapsed" :text="auth.user?.first_name" class="flex-1 min-w-0">
            <span class="block truncate text-sm text-muted">
              {{ auth.user?.first_name }}
            </span>
          </UTooltip>
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

    <nav
      class="fixed inset-x-0 bottom-0 z-40 flex border-t border-default bg-default/90 backdrop-blur lg:hidden"
      style="padding-bottom: env(safe-area-inset-bottom)"
      aria-label="Primary"
    >
      <NuxtLink
        v-for="item in items"
        :key="item.to as string"
        :to="item.to"
        class="flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] font-medium"
        :class="isActive(item.to as string) ? 'text-primary' : 'text-muted'"
      >
        <UIcon :name="item.icon!" class="size-5" />
        {{ item.label }}
      </NuxtLink>
    </nav>
  </UDashboardGroup>
</template>
