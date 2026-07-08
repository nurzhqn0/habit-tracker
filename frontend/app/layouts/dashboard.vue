<script setup lang="ts">
import type { NavigationMenuItem } from "@nuxt/ui";
import type { Preferences } from "~~/shared/types/api";
import { apiFetch } from "~/services/api/client";

const auth = useAuthStore();
const route = useRoute();
const { isMiniApp } = useTelegram();
const colorMode = useColorMode();

// Apply the user's saved theme on load so the toggle reflects their choice
// instead of the default. This wins over Telegram's scheme in the Mini App too
// — the plugin only paints the native chrome to match.
onMounted(async () => {
  const prefs = await apiFetch<Preferences>("/me/preferences").catch(() => null);
  if (prefs?.theme) colorMode.preference = prefs.theme;
});

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
          <UColorModeButton v-if="!isMiniApp" />
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
