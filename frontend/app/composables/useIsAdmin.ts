/** UI gating only — the backend ADMIN_USERNAME check is the real authorization. */
export function useIsAdmin() {
  const auth = useAuthStore();
  const adminUsername = useRuntimeConfig().public.adminUsername as string;
  return computed(
    () =>
      !!adminUsername &&
      !!auth.user?.username &&
      auth.user.username.toLowerCase() ===
        adminUsername.replace(/^@/, "").toLowerCase(),
  );
}
