<script setup lang="ts">
import type { Room } from "~~/shared/types/rooms";
import { apiFetch } from "~/services/api/client";

definePageMeta({ layout: "dashboard" });
useHead({ title: "Join room" });

const route = useRoute();
const router = useRouter();
const toast = useToast();
const view = useRoomViewStore();
const failed = ref(false);

onMounted(async () => {
  try {
    const room = await apiFetch<Room>("/rooms/join", {
      method: "POST",
      body: { code: String(route.params.code) },
    });
    toast.add({ title: `Joined ${room.name}`, color: "success" });
    view.viewedRoom = room;
    router.replace(`/app/rooms/${room.id}`);
  } catch {
    failed.value = true;
  }
});
</script>

<template>
  <div class="flex min-h-[50vh] flex-col items-center justify-center gap-4">
    <template v-if="failed">
      <UIcon name="i-lucide-link-2-off" class="size-10 text-muted" />
      <p class="font-semibold text-highlighted">Invite link is invalid or expired</p>
      <UButton to="/app/rooms" label="Back to rooms" variant="subtle" />
    </template>
    <UIcon v-else name="i-lucide-loader-circle" class="size-8 animate-spin text-muted" />
  </div>
</template>
