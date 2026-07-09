<script setup lang="ts">
import { sendInvite, type InviteResult } from "~/services/api/rooms";

const open = defineModel<boolean>("open", { required: true });

const store = useRoomStore();
const toast = useToast();

function joinLink(code: string): string {
  const botUsername = useRuntimeConfig().public.botUsername;
  return `https://t.me/${botUsername}/habitflow?startapp=join_${code}`;
}

const link = ref("");
const username = ref("");
const result = ref<InviteResult | null>(null);
const rotateBusy = ref(false);
const sendBusy = ref(false);

watch(open, (value) => {
  if (!value || !store.room) return;
  link.value = joinLink(store.room.invite_code);
  username.value = "";
  result.value = null;
});

async function copyLink() {
  await navigator.clipboard.writeText(link.value);
  toast.add({ title: "Invite link copied", color: "success" });
}

async function copyCode() {
  if (!store.room) return;
  await navigator.clipboard.writeText(store.room.invite_code);
  toast.add({ title: "Room code copied", color: "success" });
}

async function rotate() {
  rotateBusy.value = true;
  try {
    const code = await store.rotateInvite();
    link.value = joinLink(code);
    toast.add({
      title: "Link rotated — older links no longer work",
      color: "success",
    });
  } catch {
    toast.add({ title: "Could not rotate link", color: "error" });
  } finally {
    rotateBusy.value = false;
  }
}

async function sendUsernameInvite() {
  if (!username.value.trim()) return;
  sendBusy.value = true;
  try {
    result.value = await sendInvite(store.roomId, username.value);
  } catch {
    toast.add({ title: "Could not send invite", color: "error" });
  } finally {
    sendBusy.value = false;
  }
}

const shareUrl = computed(() => {
  if (!store.room) return "";
  const url = joinLink(store.room.invite_code);
  const text = `Join "${store.room.name}" on HabitFlow!`;
  return `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`;
});
</script>

<template>
  <UModal v-model:open="open" title="Invite friends">
    <template #body>
      <p class="text-muted mb-3 text-sm">
        Share this link — anyone with it can join the room.
      </p>
      <div class="flex gap-2">
        <UInput :model-value="link" readonly class="flex-1" />
        <UButton icon="i-lucide-copy" aria-label="Copy" @click="copyLink" />
        <UTooltip text="Rotate the link — older links stop working">
          <UButton
            icon="i-lucide-refresh-cw"
            color="neutral"
            variant="subtle"
            aria-label="Rotate link"
            :loading="rotateBusy"
            @click="rotate"
          />
        </UTooltip>
      </div>

      <div class="text-muted mt-3 flex items-center gap-2 text-sm">
        Room code:
        <UTooltip text="Copy room code">
          <UButton
            color="neutral"
            variant="soft"
            size="xs"
            class="font-mono"
            trailing-icon="i-lucide-copy"
            :label="store.room?.invite_code"
            @click="copyCode"
          />
        </UTooltip>
      </div>

      <USeparator label="or" class="my-4" />

      <p class="text-muted mb-3 text-sm">
        Invite by Telegram username — we'll message them if they use HabitFlow.
      </p>
      <form class="flex gap-2" @submit.prevent="sendUsernameInvite">
        <UInput v-model="username" placeholder="@username" class="flex-1" />
        <UButton
          type="submit"
          :loading="sendBusy"
          :disabled="!username.trim()"
          label="Send"
        />
      </form>

      <UAlert
        v-if="result?.status === 'sent'"
        class="mt-3"
        color="success"
        variant="subtle"
        icon="i-lucide-send"
        :title="`Invite sent to @${result.username} via Telegram.`"
      />
      <UAlert
        v-else-if="result?.status === 'not_linked'"
        class="mt-3"
        color="warning"
        variant="subtle"
        icon="i-lucide-bot-off"
        :title="`@${result.username} hasn't connected the Telegram bot.`"
        description="Share the invite link above with them directly."
      />
      <UAlert
        v-else-if="result?.status === 'already_member'"
        class="mt-3"
        color="info"
        variant="subtle"
        icon="i-lucide-user-check"
        :title="`@${result.username} is already in this room.`"
      />
      <UAlert
        v-else-if="result?.status === 'not_registered'"
        class="mt-3"
        color="info"
        variant="subtle"
        icon="i-lucide-user-plus"
        :title="`@${result.username} isn't on HabitFlow yet.`"
        description="Send them the invite link on Telegram — the room link doubles as an app invite."
      >
        <template #actions>
          <UButton
            :href="shareUrl"
            target="_blank"
            size="xs"
            icon="i-lucide-send"
            label="Share on Telegram"
          />
          <UButton
            :href="`https://t.me/${result.username}`"
            target="_blank"
            size="xs"
            color="neutral"
            variant="subtle"
            icon="i-lucide-message-circle"
            label="Open chat"
          />
        </template>
      </UAlert>
    </template>
  </UModal>
</template>
