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

/** During SSR the relative public apiBase resolves against the Nuxt server itself,
 * so use the internal base (docker network) when configured. */
function apiBaseURL(): string {
  const config = useRuntimeConfig();
  if (import.meta.server && config.apiInternalBase) return config.apiInternalBase as string;
  return config.public.apiBase;
}

export function statusOf(error: unknown): number | undefined {
  return (
    (error as { statusCode?: number })?.statusCode ??
    (error as { response?: { status?: number } })?.response?.status
  );
}

type Tokens = ReturnType<typeof useAuthTokens>;

// Composables (useCookie/useRuntimeConfig) are only safe in the synchronous
// part of a request on the server, so apiBase and token refs are captured at
// apiFetch entry and passed down — never resolved after an await.
async function doRefresh(apiBase: string, tokens: Tokens): Promise<boolean> {
  if (!tokens.refresh.value) return false;

  try {
    const response = await $fetch<TokenResponse>("/auth/refresh", {
      baseURL: apiBase,
      method: "POST",
      body: { refresh_token: tokens.refresh.value },
    });
    tokens.access.value = response.access_token;
    tokens.refresh.value = response.refresh_token;
    return true;
  } catch (error) {
    // Only a definitive rejection ends the session. Transient failures
    // (network, 5xx, 429) keep the tokens so a later request can retry.
    const status = statusOf(error);
    if (status === 401 || status === 403) {
      tokens.access.value = null;
      tokens.refresh.value = null;
    }
    return false;
  }
}

let refreshing: Promise<boolean> | null = null;

async function tryRefresh(apiBase: string, tokens: Tokens): Promise<boolean> {
  // The server runtime is shared across concurrent requests of different
  // users — never share an in-flight refresh promise there.
  if (import.meta.server) return doRefresh(apiBase, tokens);
  refreshing ??= doRefresh(apiBase, tokens).finally(() => {
    refreshing = null;
  });
  return refreshing;
}

/** $fetch against the API with bearer auth; on 401 refreshes once and retries. */
export async function apiFetch<T>(
  path: string,
  options: Parameters<typeof $fetch>[1] = {},
): Promise<T> {
  const apiBase = apiBaseURL();
  const tokens = useAuthTokens();

  const doFetch = () =>
    $fetch<T>(path, {
      baseURL: apiBase,
      ...options,
      headers: {
        ...(options.headers as Record<string, string> | undefined),
        ...(tokens.access.value ? { Authorization: `Bearer ${tokens.access.value}` } : {}),
      },
    });

  try {
    return (await doFetch()) as T;
  } catch (error: unknown) {
    if (statusOf(error) === 401 && (await tryRefresh(apiBase, tokens))) {
      return (await doFetch()) as T;
    }
    throw error;
  }
}
