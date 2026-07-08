// Telegram Mini App integration. When the frontend is opened inside Telegram,
// the injected WebApp SDK carries a signed `initData`; we verify it on the
// backend to sign the user in, and adopt Telegram's theme + native chrome.

function loadSdk(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (window.Telegram?.WebApp) return resolve();
    const script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-web-app.js";
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Telegram SDK failed to load"));
    document.head.appendChild(script);
  });
}

export default defineNuxtPlugin(async () => {
  try {
    await loadSdk();
  } catch {
    return; // Not reachable / blocked — behave as a normal web app.
  }

  const wa = window.Telegram?.WebApp;
  if (!wa?.initData) return; // Opened outside Telegram — nothing native to do.

  const { isMiniApp } = useTelegram();
  isMiniApp.value = true;

  wa.ready();
  wa.expand();
  wa.disableVerticalSwipes?.();
  wa.enableClosingConfirmation();

  // Paint Telegram's native chrome to match the app's resolved theme. The
  // theme itself follows the user's saved preference (applied by the dashboard
  // layout) — Telegram's own scheme must not override the user's choice. These
  // hexes mirror --ui-bg (see assets/css/main.css) for light and dark.
  const colorMode = useColorMode();
  const paintChrome = () => {
    const bg = colorMode.value === "dark" ? "#1c1917" : "#fbfbfa";
    wa.setBackgroundColor?.(bg);
    wa.setHeaderColor?.(bg);
  };
  watch(() => colorMode.value, paintChrome, { immediate: true });

  // Sign in with initData if there is no existing session.
  const auth = useAuthStore();
  if (!auth.ready) await auth.restore();
  if (!auth.isLoggedIn) {
    try {
      await auth.loginWithTelegramMiniApp(wa.initData);
    } catch {
      // Fall through — the normal login UI still renders.
    }
  }

  const router = useRouter();

  // No marketing landing inside Telegram — go straight to the app.
  // Handle deep links: startapp=join_{code} navigates to the room join page.
  // Navigating here (during plugin init) races Nuxt's initial navigation and
  // is silently dropped, so defer to app:mounted when the router is free.
  if (auth.isLoggedIn) {
    const startParam = wa.initDataUnsafe?.start_param;
    const target = startParam?.startsWith("join_")
      ? `/app/rooms/join/${startParam.slice(5)}`
      : useRoute().path === "/"
        ? "/app"
        : null;
    if (target) {
      useNuxtApp().hooks.hookOnce("app:mounted", () => {
        navigateTo(target);
      });
    }
  }
  // Native back button: shown on any nested /app page, hidden on the roots.
  const back = () => router.back();
  wa.BackButton.onClick(back);
  const ROOTS = new Set(["/app", "/app/rooms", "/app/settings", "/"]);
  const syncBackButton = (path: string) => {
    if (path.startsWith("/app") && !ROOTS.has(path)) wa.BackButton.show();
    else wa.BackButton.hide();
  };
  syncBackButton(useRoute().path);
  router.afterEach((to) => syncBackButton(to.path));
});
