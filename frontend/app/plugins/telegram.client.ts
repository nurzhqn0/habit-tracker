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

  // Adopt Telegram's light/dark scheme and paint the native chrome to match.
  const colorMode = useColorMode();
  const applyTheme = () => {
    colorMode.preference = wa.colorScheme;
    const bg = wa.themeParams.bg_color;
    if (bg) {
      wa.setBackgroundColor?.(bg);
      wa.setHeaderColor?.(bg);
    }
  };
  applyTheme();
  wa.onEvent("themeChanged", applyTheme);

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

  // Native back button: shown on any nested /app page, hidden on the roots.
  const router = useRouter();
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
