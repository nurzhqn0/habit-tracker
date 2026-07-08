<script setup lang="ts">
// Completes the redirect (authorization code) Telegram login started by
// TelegramLoginButton when the popup flow is unavailable (in-app webviews).

const route = useRoute();
const auth = useAuthStore();
const error = ref("");

useSeoMeta({ title: "Signing in…", robots: "noindex" });

onMounted(async () => {
  const code = typeof route.query.code === "string" ? route.query.code : "";
  const state = typeof route.query.state === "string" ? route.query.state : "";
  const raw = sessionStorage.getItem("hf_tg_oidc");
  sessionStorage.removeItem("hf_tg_oidc");

  let saved: { verifier?: string; state?: string; target?: string } = {};
  try {
    saved = raw ? JSON.parse(raw) : {};
  } catch {
    saved = {};
  }

  if (!code || !state || !saved.verifier || saved.state !== state) {
    error.value = "Login was cancelled or the link is no longer valid.";
    return;
  }

  try {
    await auth.loginWithTelegramCode(code, saved.verifier, `${location.origin}/auth/callback`);
    const target =
      typeof saved.target === "string" && saved.target.startsWith("/app") ? saved.target : "/app";
    await navigateTo(target, { replace: true });
  } catch {
    error.value = "Could not verify Telegram data. Please try again.";
  }
});
</script>

<template>
  <div class="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
    <template v-if="!error">
      <UIcon name="i-lucide-loader-circle" class="size-8 animate-spin text-primary" />
      <p class="text-muted">Signing you in with Telegram…</p>
    </template>
    <template v-else>
      <UIcon name="i-lucide-circle-alert" class="size-8 text-error" />
      <p class="max-w-xs text-muted">{{ error }}</p>
      <UButton to="/app" label="Back to app" color="neutral" variant="subtle" />
    </template>
  </div>
</template>
