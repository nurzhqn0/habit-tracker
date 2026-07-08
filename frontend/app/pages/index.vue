<script setup lang="ts">
// This is a Telegram mini app — no marketing landing needed.
// Redirect straight to the dashboard.
await navigateTo("/app", { replace: true, redirectCode: 301 });
</script>
