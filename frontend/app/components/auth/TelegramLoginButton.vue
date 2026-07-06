<script setup lang="ts">
// New Telegram Login (OIDC): https://oauth.telegram.org/js/telegram-login.js?5
// Popup flow returns an id_token JWT that the backend verifies against Telegram's JWKS.

const { tgClientId } = useRuntimeConfig().public;
const auth = useAuthStore();
const toast = useToast();
const ready = ref(false);

async function onAuth(data: { id_token?: string; error?: string }) {
  if (!data?.id_token) {
    if (data?.error) toast.add({ title: "Login failed", description: data.error, color: "error" });
    return;
  }
  try {
    await auth.loginWithTelegram(data.id_token);
    navigateTo("/app");
  } catch {
    toast.add({ title: "Login failed", description: "Could not verify Telegram data.", color: "error" });
  }
}

function openLogin() {
  (window as any).Telegram?.Login?.open();
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
  if (!tgClientId) return;
  const script = document.createElement("script");
  script.src = "https://oauth.telegram.org/js/telegram-login.js?5";
  script.async = true;
  script.onload = () => {
    (window as any).Telegram?.Login?.init(
      { client_id: Number(tgClientId), scope: ["profile", "write"] },
      onAuth,
    );
    ready.value = true;
  };
  document.head.appendChild(script);
});
</script>

<template>
  <div class="flex flex-col items-center gap-3">
    <UButton
      v-if="tgClientId"
      size="xl"
      icon="i-lucide-send"
      label="Sign in with Telegram"
      :loading="!ready"
      @click="openLogin"
    />
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
