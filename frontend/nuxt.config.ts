export default defineNuxtConfig({
  compatibilityDate: "2026-07-06",
  modules: ["@nuxt/ui", "@pinia/nuxt"],
  css: ["~/assets/css/main.css"],
  devtools: { enabled: false },
  runtimeConfig: {
    public: {
      apiBase: "http://localhost:8000/api/v1",
      botUsername: "",
    },
  },
});
