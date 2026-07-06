export default defineNuxtConfig({
  compatibilityDate: "2026-07-06",
  modules: ["@nuxt/ui", "@pinia/nuxt"],
  css: ["~/assets/css/main.css"],
  devtools: { enabled: false },
  app: {
    head: {
      htmlAttrs: { lang: "en" },
      titleTemplate: (title?: string) => (title ? `${title} · HabitFlow` : "HabitFlow — Make consistency visible"),
      meta: [
        {
          name: "description",
          content:
            "Track yes/no and measurable habits, watch your habit strength grow, and stay accountable with friends — with reminders delivered by Telegram.",
        },
        { name: "theme-color", content: "#111111" },
      ],
      link: [
        { rel: "icon", type: "image/svg+xml", href: "/icon.svg" },
        { rel: "icon", href: "/favicon.ico", sizes: "32x32" },
        { rel: "apple-touch-icon", href: "/apple-touch-icon.png" },
      ],
    },
  },
  icon: {
    clientBundle: { scan: true },
  },
  runtimeConfig: {
    apiInternalBase: "", // NUXT_API_INTERNAL_BASE — SSR-only API base (docker network)
    public: {
      apiBase: "http://localhost:8000/api/v1",
      botUsername: "",
      tgClientId: "", // BotFather -> Web Login -> Client ID
    },
  },
});
