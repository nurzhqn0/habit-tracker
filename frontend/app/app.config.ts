export default defineAppConfig({
  ui: {
    colors: {
      primary: "emerald",
      neutral: "stone",
    },
    dashboardPanel: {
      slots: {
        // Mobile: let scrolled content clear the fixed bottom nav (+ notch inset).
        body: "pb-[calc(5rem+env(safe-area-inset-bottom))] lg:pb-6",
      },
    },
  },
});
