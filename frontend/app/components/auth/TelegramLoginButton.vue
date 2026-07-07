<script setup lang="ts">
// New Telegram Login (OIDC): https://oauth.telegram.org/js/telegram-login.js?5
// Popup flow returns an id_token JWT that the backend verifies against Telegram's JWKS.

const { tgClientId } = useRuntimeConfig().public;
const auth = useAuthStore();
const toast = useToast();
const route = useRoute();
const ready = ref(false);

function afterLogin() {
  const redirect = route.query.redirect;
  const target = typeof redirect === "string" && redirect.startsWith("/app") ? redirect : "/app";
  navigateTo(target);
}

async function onAuth(data: { id_token?: string; error?: string }) {
  if (!data?.id_token) {
    if (data?.error) toast.add({ title: "Login failed", description: data.error, color: "error" });
    return;
  }
  try {
    await auth.loginWithTelegram(data.id_token);
    afterLogin();
  } catch {
    toast.add({ title: "Login failed", description: "Could not verify Telegram data.", color: "error" });
  }
}

function base64url(bytes: Uint8Array): string {
  return btoa(String.fromCharCode(...bytes))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

// Full-page authorization-code flow (PKCE) for browsers that block popups,
// e.g. Telegram's in-app Safari sheet. Completed by /auth/callback.
async function startRedirectLogin() {
  const verifier = base64url(crypto.getRandomValues(new Uint8Array(32)));
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier));
  const state = base64url(crypto.getRandomValues(new Uint8Array(16)));
  const target = typeof route.query.redirect === "string" ? route.query.redirect : "";
  sessionStorage.setItem("hf_tg_oidc", JSON.stringify({ verifier, state, target }));
  const params = new URLSearchParams({
    client_id: String(tgClientId),
    redirect_uri: `${location.origin}/auth/callback`,
    response_type: "code",
    scope: "openid profile telegram:bot_access",
    state,
    code_challenge: base64url(new Uint8Array(digest)),
    code_challenge_method: "S256",
  });
  location.href = `https://oauth.telegram.org/auth?${params.toString()}`;
}

async function openLogin() {
  const login = (window as any).Telegram?.Login;
  if (!login) {
    toast.add({
      title: "Telegram login is not available",
      description: "The Telegram widget could not load. Check your connection or ad blocker.",
      color: "error",
    });
    return;
  }
  // In-app webviews return null from window.open and the widget then silently
  // does nothing. Watch the call so we can fall back to the redirect flow.
  // (Telegram's own browser signs in natively without window.open — untouched.)
  const originalOpen = window.open;
  let popup: Window | null | undefined;
  window.open = function (...args: Parameters<typeof window.open>) {
    popup = originalOpen.apply(window, args);
    return popup;
  };
  try {
    login.open();
  } finally {
    window.open = originalOpen;
  }
  if (popup === null) await startRedirectLogin();
}

async function devLogin() {
  try {
    await auth.loginTestMode();
    afterLogin();
  } catch {
    toast.add({ title: "Dev login failed", description: "Backend TEST_MODE is off.", color: "error" });
  }
}

const failed = ref(false);

function initWidget() {
  (window as any).Telegram.Login.init(
    { client_id: Number(tgClientId), scope: ["profile", "write"] },
    onAuth,
  );
  ready.value = true;
}

let loadTimer: ReturnType<typeof setTimeout> | undefined;

function mountWidget() {
  failed.value = false;
  // Script may already be present from a previous visit to this page.
  if ((window as any).Telegram?.Login) {
    initWidget();
    return;
  }
  // A stalled request fires neither onload nor onerror, which used to leave
  // the button disabled (spinner) forever — surface the retry UI instead.
  clearTimeout(loadTimer);
  loadTimer = setTimeout(() => {
    if (!ready.value) failed.value = true;
  }, 8000);
  const script = document.createElement("script");
  script.src = "https://oauth.telegram.org/js/telegram-login.js?5";
  script.async = true;
  script.onload = () => {
    clearTimeout(loadTimer);
    if ((window as any).Telegram?.Login) initWidget();
    else failed.value = true;
  };
  script.onerror = () => {
    clearTimeout(loadTimer);
    script.remove();
    failed.value = true;
  };
  document.head.appendChild(script);
}

onMounted(() => {
  if (tgClientId) mountWidget();
});

onUnmounted(() => clearTimeout(loadTimer));
</script>

<template>
  <div class="flex flex-col items-center gap-3">
    <template v-if="tgClientId">
      <UButton
        v-if="!failed"
        size="xl"
        icon="i-lucide-send"
        label="Sign in with Telegram"
        :loading="!ready"
        @click="openLogin"
      />
      <template v-else>
        <UButton
          size="xl"
          icon="i-lucide-refresh-cw"
          label="Retry Telegram login"
          color="neutral"
          variant="subtle"
          @click="mountWidget"
        />
        <p class="max-w-xs text-center text-xs text-muted">
          The Telegram widget could not load — check your connection or ad blocker.
        </p>
      </template>
    </template>
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
