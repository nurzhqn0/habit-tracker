export default defineNuxtRouteMiddleware(async (to) => {
  if (!to.path.startsWith("/app")) return;

  const auth = useAuthStore();
  if (!auth.ready) await auth.restore();
  if (auth.isLoggedIn) return;

  // Not ready here means /me failed transiently (backend restart, network
  // blip) — let the user in and retry on the next navigation. A definitive
  // rejection (or no tokens at all) leaves the store ready with no user.
  if (auth.ready) return navigateTo("/");
});
