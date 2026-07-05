<script setup lang="ts">
// Placeholder — replaced by the checkmark grid main screen in Phase 3.
const auth = useAuthStore();
</script>

<template>
  <div class="mx-auto max-w-3xl p-8">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-highlighted">Welcome, {{ auth.user?.first_name }}</h1>
      <UButton color="neutral" variant="ghost" icon="i-lucide-log-out" label="Logout" @click="auth.logout()" />
    </div>
    <p class="mt-2 text-muted">Habit grid coming in Phase 3.</p>
  </div>
</template>
