import { apiFetch, statusOf, useAuthTokens } from "~/services/api/client";

export function useDownload() {
  const toast = useToast();
  const { apiBase } = useRuntimeConfig().public;
  const downloading = ref(false);
  const sending = ref(false);

  /** Generates the export server-side and has the Telegram bot deliver it to
   * the user's chat, instead of downloading in the browser. */
  async function sendToTelegram(path: string, query?: Record<string, string>) {
    sending.value = true;
    try {
      await apiFetch(path, { query: { ...query, to_telegram: "1" } });
      toast.add({
        title: "Sent to Telegram",
        description: "The bot delivered your export — check the chat.",
        icon: "i-lucide-send",
        color: "success",
      });
    } catch (error) {
      const description =
        statusOf(error) === 422
          ? "Connect the Telegram bot in Settings first, then export again."
          : "Could not deliver the export. Please try again.";
      toast.add({ title: "Export failed", description, color: "error" });
    } finally {
      sending.value = false;
    }
  }

  async function download(path: string, filename: string, query?: Record<string, string>) {
    const { access } = useAuthTokens();
    downloading.value = true;
    try {
      const blob = await $fetch<Blob>(path, {
        baseURL: apiBase as string,
        responseType: "blob",
        query,
        headers: access.value ? { Authorization: `Bearer ${access.value}` } : {},
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.add({ title: "Export failed", color: "error" });
    } finally {
      downloading.value = false;
    }
  }

  return { download, downloading, sendToTelegram, sending };
}
