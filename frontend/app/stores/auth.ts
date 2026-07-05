import { defineStore } from "pinia";
import type { TelegramAuthPayload, TokenResponse, User } from "~~/shared/types/api";
import { apiFetch, useAuthTokens } from "~/services/api/client";

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

    async loginWithTelegram(payload: TelegramAuthPayload) {
      const response = await apiFetch<TokenResponse>("/auth/telegram", {
        method: "POST",
        body: payload,
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
        } catch {
          this.user = null;
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
