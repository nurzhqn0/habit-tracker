// Dev-only: the app authenticates exclusively through Telegram (Mini App
// initData or the OIDC redirect), so a plain browser on localhost has no way
// to log in. During `nuxt dev` — and only then — sign in via the backend's
// TEST_MODE endpoint so every feature is usable at http://localhost:3000.
//
// import.meta.dev is false in the production build (node .output), so this
// plugin does not exist in prod at all.
export default defineNuxtPlugin(async () => {
  if (!import.meta.dev) return;
  // Inside a real Telegram webview, let telegram.client.ts handle auth.
  if (window.Telegram?.WebApp?.initData) return;

  const auth = useAuthStore();
  if (!auth.ready) await auth.restore();
  if (!auth.isLoggedIn) await auth.loginTestMode().catch(() => {});
});
