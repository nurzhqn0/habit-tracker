import { useAuthTokens } from "~/services/api/client";

export function useDownload() {
  const toast = useToast();
  const { apiBase } = useRuntimeConfig().public;
  const downloading = ref(false);

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

  return { download, downloading };
}
