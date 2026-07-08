import type { TelegramWebApp } from "~~/shared/types/telegram";

type Impact = "light" | "medium" | "heavy" | "rigid" | "soft";
type Notify = "error" | "success" | "warning";

/** Access to the Telegram Mini App SDK. Safe to call outside Telegram —
 * `isMiniApp` is false and the haptic helpers become no-ops. */
export function useTelegram() {
  // Set true by the telegram.client plugin once a real initData is present.
  const isMiniApp = useState("tg-miniapp", () => false);

  const webApp = (): TelegramWebApp | undefined =>
    import.meta.client ? window.Telegram?.WebApp : undefined;

  function impact(style: Impact = "light") {
    if (isMiniApp.value) webApp()?.HapticFeedback.impactOccurred(style);
  }
  function notify(type: Notify) {
    if (isMiniApp.value) webApp()?.HapticFeedback.notificationOccurred(type);
  }
  function selection() {
    if (isMiniApp.value) webApp()?.HapticFeedback.selectionChanged();
  }

  return { isMiniApp, webApp, impact, notify, selection };
}
