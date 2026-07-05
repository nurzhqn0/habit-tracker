import type { TokenResponse } from "~~/shared/types/api";

const ACCESS_COOKIE = "hf_access";
const REFRESH_COOKIE = "hf_refresh";

export function useAuthTokens() {
  const access = useCookie<string | null>(ACCESS_COOKIE, {
    maxAge: 60 * 60 * 24 * 30,
    sameSite: "lax",
  });
  const refresh = useCookie<string | null>(REFRESH_COOKIE, {
    maxAge: 60 * 60 * 24 * 30,
    sameSite: "lax",
  });
  return { access, refresh };
}

let refreshing: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  const { apiBase } = useRuntimeConfig().public;
  const { access, refresh } = useAuthTokens();
  if (!refresh.value) return false;

  refreshing ??= (async () => {
    try {
      const response = await $fetch<TokenResponse>("/auth/refresh", {
        baseURL: apiBase,
        method: "POST",
        body: { refresh_token: refresh.value },
      });
      access.value = response.access_token;
      refresh.value = response.refresh_token;
      return true;
    } catch {
      access.value = null;
      refresh.value = null;
      return false;
    } finally {
      refreshing = null;
    }
  })();
  return refreshing;
}

/** $fetch against the API with bearer auth; on 401 refreshes once and retries. */
export async function apiFetch<T>(
  path: string,
  options: Parameters<typeof $fetch>[1] = {},
): Promise<T> {
  const { apiBase } = useRuntimeConfig().public;
  const { access } = useAuthTokens();

  const doFetch = () =>
    $fetch<T>(path, {
      baseURL: apiBase,
      ...options,
      headers: {
        ...(options.headers as Record<string, string> | undefined),
        ...(access.value ? { Authorization: `Bearer ${access.value}` } : {}),
      },
    });

  try {
    return (await doFetch()) as T;
  } catch (error: unknown) {
    const status = (error as { statusCode?: number; response?: { status?: number } })?.statusCode
      ?? (error as { response?: { status?: number } })?.response?.status;
    if (status === 401 && (await tryRefresh())) {
      return (await doFetch()) as T;
    }
    throw error;
  }
}
