<script setup lang="ts">
const auth = useAuthStore();

onMounted(() => {
  if (!auth.ready) auth.restore();
});

const features = [
  {
    icon: "i-lucide-flame",
    title: "Streaks & scores",
    description: "The proven uHabits strength algorithm — every check-in strengthens your habit.",
  },
  {
    icon: "i-lucide-calendar-days",
    title: "Flexible schedules",
    description: "Daily, 3× per week, every N days — plus measurable habits with targets and units.",
  },
  {
    icon: "i-lucide-users",
    title: "Rooms with friends",
    description: "Share habits in rooms, climb the leaderboard, keep each other accountable.",
  },
  {
    icon: "i-lucide-send",
    title: "Telegram reminders",
    description: "The bot pings you at the right time. Mark done right from the chat.",
  },
];
</script>

<template>
  <div class="min-h-screen">
    <header class="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
      <span class="text-lg font-bold text-highlighted">HabitFlow</span>
      <div class="flex items-center gap-2">
        <UColorModeButton />
        <UButton v-if="auth.isLoggedIn" to="/app" label="Open app" trailing-icon="i-lucide-arrow-right" />
      </div>
    </header>

    <main class="mx-auto max-w-5xl px-6">
      <section class="flex flex-col items-center gap-6 py-20 text-center">
        <UBadge label="Loop Habit Tracker, rebuilt for the web" variant="subtle" />
        <h1 class="max-w-2xl text-5xl font-bold tracking-tight text-highlighted">
          Make consistency visible.
        </h1>
        <p class="max-w-xl text-lg text-muted">
          Track yes/no and measurable habits, watch your habit strength grow, and stay
          accountable with friends — with reminders delivered by Telegram.
        </p>
        <div class="mt-2">
          <UButton v-if="auth.isLoggedIn" to="/app" size="xl" label="Open dashboard" />
          <AuthTelegramLoginButton v-else />
        </div>
      </section>

      <section class="grid gap-4 pb-24 sm:grid-cols-2">
        <UCard v-for="feature in features" :key="feature.title">
          <div class="flex items-start gap-3">
            <UIcon :name="feature.icon" class="mt-1 size-6 text-primary" />
            <div>
              <p class="font-semibold text-highlighted">{{ feature.title }}</p>
              <p class="mt-1 text-sm text-muted">{{ feature.description }}</p>
            </div>
          </div>
        </UCard>
      </section>
    </main>

    <footer class="border-t border-default py-6 text-center text-sm text-muted">
      devhouse.kz @2026
    </footer>
  </div>
</template>
