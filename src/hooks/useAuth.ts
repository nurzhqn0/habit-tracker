"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AUTH_COOKIE_MAX_AGE_SECONDS,
  AUTH_EMAIL_COOKIE,
  AUTH_TOKEN_COOKIE,
} from "../lib/auth-cookies";
import type { AuthState, UseAuthResult } from "../types/auth";

const AUTH_CHANGE_EVENT = "habitflow-auth-change";

function getCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null;
  }

  const escapedName = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = document.cookie.match(
    new RegExp(`(?:^|; )${escapedName}=([^;]*)`),
  );
  return match ? decodeURIComponent(match[1]) : null;
}

function setCookie(name: string, value: string, maxAgeSeconds: number): void {
  document.cookie = `${name}=${encodeURIComponent(value)}; Path=/; Max-Age=${maxAgeSeconds}; SameSite=Lax`;
}

function clearCookie(name: string): void {
  document.cookie = `${name}=; Path=/; Max-Age=0; SameSite=Lax`;
}

export function useAuth(): UseAuthResult {
  const [state, setState] = useState<AuthState>({
    isReady: false,
    isLoggedIn: false,
    email: null,
  });

  const refresh = useCallback(() => {
    const token = getCookie(AUTH_TOKEN_COOKIE);
    const email = getCookie(AUTH_EMAIL_COOKIE);
    setState({
      isReady: true,
      isLoggedIn: Boolean(token),
      email: email ?? null,
    });
  }, []);

  const emitAuthChange = useCallback(() => {
    window.dispatchEvent(new Event(AUTH_CHANGE_EVENT));
  }, []);

  const login = useCallback(
    (email: string) => {
      const normalizedEmail = email.trim().toLowerCase();
      const token = `${Date.now()}-${Math.random().toString(36).slice(2)}`;

      setCookie(AUTH_TOKEN_COOKIE, token, AUTH_COOKIE_MAX_AGE_SECONDS);
      setCookie(
        AUTH_EMAIL_COOKIE,
        normalizedEmail,
        AUTH_COOKIE_MAX_AGE_SECONDS,
      );
      refresh();
      emitAuthChange();
    },
    [emitAuthChange, refresh],
  );

  const logout = useCallback(() => {
    clearCookie(AUTH_TOKEN_COOKIE);
    clearCookie(AUTH_EMAIL_COOKIE);
    refresh();
    emitAuthChange();
  }, [emitAuthChange, refresh]);

  useEffect(() => {
    refresh();

    window.addEventListener("focus", refresh);
    window.addEventListener(AUTH_CHANGE_EVENT, refresh);

    return () => {
      window.removeEventListener("focus", refresh);
      window.removeEventListener(AUTH_CHANGE_EVENT, refresh);
    };
  }, [refresh]);

  return {
    ...state,
    login,
    logout,
    refresh,
  };
}
