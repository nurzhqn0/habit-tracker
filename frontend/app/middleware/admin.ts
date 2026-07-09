export default defineNuxtRouteMiddleware(() => {
  const auth = useAuthStore();
  // Null user means /me failed transiently (see auth.global.ts) — let the
  // page load; the backend 403 is the real gate.
  if (auth.user && !useIsAdmin().value) return navigateTo("/app");
});
