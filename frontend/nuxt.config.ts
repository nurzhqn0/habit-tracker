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
          name: "viewport",
          content: "width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover",
        },
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
      adminUsername: "", // NUXT_PUBLIC_ADMIN_USERNAME — UI gating only, backend enforces
    },
  },
  // Dev-only: lets you serve `npm run dev` behind an HTTPS tunnel (Telegram
  // requires https). Set NUXT_PUBLIC_API_BASE=/api/v1 so the browser calls the
  // same (https) origin; this proxy forwards /api to the Dockerized api, so no
  // mixed-content and no CORS. allowedHosts lets the tunnel domain reach Vite.
  $development: {
    nitro: {
      devProxy: {
        "/api": { target: "http://localhost:8000/api", changeOrigin: true },
      },
    },
    vite: {
      server: { allowedHosts: true },
    },
  },
});
