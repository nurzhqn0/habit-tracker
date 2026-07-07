import { defineStore } from "pinia";
import type { TokenResponse, User } from "~~/shared/types/api";
import { apiFetch, statusOf, useAuthTokens } from "~/services/api/client";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null as User | null,
    ready: false,
  }),
  getters: {
    isLoggedIn: (state) => state.user !== null,
  },
  actions: {
    _applyTokens(response: TokenResponse) {
      const { access, refresh } = useAuthTokens();
      access.value = response.access_token;
      refresh.value = response.refresh_token;
      this.user = response.user;
    },

    async loginWithTelegram(idToken: string) {
      const response = await apiFetch<TokenResponse>("/auth/telegram", {
        method: "POST",
        body: { id_token: idToken },
      });
      this._applyTokens(response);
    },

    /** Redirect (authorization code) flow — used where popups are blocked. */
    async loginWithTelegramCode(code: string, codeVerifier: string, redirectUri: string) {
      const response = await apiFetch<TokenResponse>("/auth/telegram/code", {
        method: "POST",
        body: { code, code_verifier: codeVerifier, redirect_uri: redirectUri },
      });
      this._applyTokens(response);
    },

    async loginTestMode() {
      const response = await apiFetch<TokenResponse>("/auth/test-login", { method: "POST" });
      this._applyTokens(response);
    },

    /** Loads the current user if a token exists. Safe to call on app start. */
    async restore() {
      const { access, refresh } = useAuthTokens();
      if (access.value || refresh.value) {
        try {
          this.user = await apiFetch<User>("/me");
        } catch (error) {
          this.user = null;
          const status = statusOf(error);
          // Transient failure (network, 5xx): stay not-ready so the next
          // navigation retries instead of treating it as logged out.
          if (status !== 401 && status !== 403) return;
        }
      }
      this.ready = true;
    },

    async logout() {
      const { access, refresh } = useAuthTokens();
      if (refresh.value) {
        await apiFetch("/auth/logout", {
          method: "POST",
          body: { refresh_token: refresh.value },
        }).catch(() => {});
      }
      access.value = null;
      refresh.value = null;
      this.user = null;
      navigateTo("/");
    },
  },
});
