export default defineNuxtRouteMiddleware(async (to) => {
  if (!to.path.startsWith("/app")) return;

  const auth = useAuthStore();
  if (!auth.ready) await auth.restore();
  if (!auth.isLoggedIn) return navigateTo("/");
});
