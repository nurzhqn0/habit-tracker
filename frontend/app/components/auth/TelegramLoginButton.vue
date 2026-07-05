<script setup lang="ts">
import type { TelegramAuthPayload } from "~~/shared/types/api";

const { botUsername } = useRuntimeConfig().public;
const auth = useAuthStore();
const toast = useToast();
const container = ref<HTMLDivElement>();

async function onAuth(payload: TelegramAuthPayload) {
  try {
    await auth.loginWithTelegram(payload);
    navigateTo("/app");
  } catch {
    toast.add({ title: "Login failed", description: "Could not verify Telegram data.", color: "error" });
  }
}

async function devLogin() {
  try {
    await auth.loginTestMode();
    navigateTo("/app");
  } catch {
    toast.add({ title: "Dev login failed", description: "Backend TEST_MODE is off.", color: "error" });
  }
}

onMounted(() => {
  if (!botUsername) return;
  (window as any).onTelegramAuth = onAuth;
  const script = document.createElement("script");
  script.src = "https://telegram.org/js/telegram-widget.js?22";
  script.async = true;
  script.setAttribute("data-telegram-login", botUsername as string);
  script.setAttribute("data-size", "large");
  script.setAttribute("data-radius", "12");
  script.setAttribute("data-onauth", "onTelegramAuth(user)");
  script.setAttribute("data-request-access", "write");
  container.value?.appendChild(script);
});
</script>

<template>
  <div class="flex flex-col items-center gap-3">
    <div v-if="botUsername" ref="container" />
    <UButton
      v-else
      icon="i-lucide-flask-conical"
      label="Dev login (TEST_MODE)"
      color="neutral"
      variant="subtle"
      @click="devLogin"
    />
  </div>
</template>
