<script setup lang="ts">
const auth = useAuthStore();

useSeoMeta({
  title: "HabitFlow — Make consistency visible",
  description:
    "Track yes/no and measurable habits, watch your habit strength grow, and stay accountable with friends — with reminders delivered by Telegram.",
  ogTitle: "HabitFlow — Make consistency visible",
  ogDescription:
    "Habit tracking with streaks, scores, rooms with friends, and Telegram reminders.",
  ogType: "website",
  ogUrl: "https://habitflow.nurzhqn.com/",
  ogImage: "https://habitflow.nurzhqn.com/og.png",
  twitterCard: "summary_large_image",
});
useHead({
  titleTemplate: "%s", // landing title already includes the brand
  link: [{ rel: "canonical", href: "https://habitflow.nurzhqn.com/" }],
});

onMounted(() => {
  if (!auth.ready) auth.restore();
});

const features = [
  {
    icon: "i-lucide-flame",
    title: "Streaks & scores",
    description:
      "The proven uHabits strength algorithm — every check-in strengthens your habit, every miss decays it honestly.",
    wide: true,
  },
  {
    icon: "i-lucide-calendar-days",
    title: "Flexible schedules",
    description: "Daily, 3× per week, every N days — plus measurable habits with targets and units.",
    wide: false,
  },
  {
    icon: "i-lucide-users",
    title: "Rooms with friends",
    description: "Share habits in rooms, climb the leaderboard, keep each other accountable.",
    wide: false,
  },
  {
    icon: "i-lucide-send",
    title: "Telegram reminders",
    description: "The bot pings you at the right time. Mark done right from the chat — no app switch.",
    wide: true,
  },
];
</script>

<template>
  <div class="min-h-screen">
    <header class="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
      <span class="flex items-center gap-2 font-semibold tracking-tight text-highlighted">
        <UIcon name="i-lucide-activity" class="size-5 text-primary" />
        HabitFlow
      </span>
      <div class="flex items-center gap-2">
        <UColorModeButton />
        <UButton
          v-if="auth.isLoggedIn"
          to="/app"
          label="Open app"
          color="neutral"
          variant="outline"
          trailing-icon="i-lucide-arrow-right"
        />
      </div>
    </header>

    <main class="mx-auto max-w-5xl px-6">
      <section class="flex flex-col items-center gap-7 py-24 text-center sm:py-32">
        <p
          class="fade-up rounded-full border border-default px-3 py-1 text-xs uppercase tracking-[0.08em] text-muted"
        >
          Loop Habit Tracker, rebuilt for the web
        </p>
        <h1
          class="fade-up max-w-3xl font-serif text-5xl leading-[1.1] tracking-[-0.02em] text-highlighted sm:text-6xl"
          style="--stagger: 1"
        >
          Make consistency visible.
        </h1>
        <p class="fade-up max-w-xl text-lg leading-relaxed text-muted" style="--stagger: 2">
          Track yes/no and measurable habits, watch your habit strength grow, and stay
          accountable with friends — with reminders delivered by Telegram.
        </p>
        <div class="fade-up mt-2" style="--stagger: 3">
          <UButton v-if="auth.isLoggedIn" to="/app" size="xl" label="Open dashboard" />
          <AuthTelegramLoginButton v-else />
        </div>
      </section>

      <section class="grid gap-4 pb-28 sm:grid-cols-3">
        <div
          v-for="(feature, index) in features"
          :key="feature.title"
          class="fade-up rounded-lg border border-default bg-default p-7 sm:p-8"
          :class="feature.wide ? 'sm:col-span-2' : ''"
          :style="{ '--stagger': index + 1 }"
        >
          <span class="inline-flex rounded-md bg-elevated p-2">
            <UIcon :name="feature.icon" class="size-5 text-primary" />
          </span>
          <p class="mt-4 font-semibold text-highlighted">{{ feature.title }}</p>
          <p class="mt-1.5 text-sm leading-relaxed text-muted">{{ feature.description }}</p>
        </div>
      </section>
    </main>

    <footer
      class="mx-auto flex max-w-5xl items-center justify-between border-t border-default px-6 py-8 text-sm text-muted"
    >
      <span>HabitFlow</span>
      <span>devhouse.kz © 2026</span>
    </footer>
  </div>
</template>
