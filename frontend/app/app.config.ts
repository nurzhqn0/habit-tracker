export default defineAppConfig({
  ui: {
    colors: {
      primary: "emerald",
      neutral: "stone",
    },
    dashboardNavbar: {
      slots: {
        // Grow the header by the top inset so the app bg fills the notch /
        // Telegram fullscreen controls and the title row sits clear below them.
        root: "h-auto min-h-(--ui-header-height) pt-[var(--app-inset-top)]",
      },
    },
    dashboardPanel: {
      slots: {
        // Mobile: let scrolled content clear the fixed bottom nav (+ notch inset).
        body: "pb-[calc(5rem+var(--app-inset-bottom))] lg:pb-6",
      },
    },
  },
});
