<script setup lang="ts">
import type { FeedEvent } from "~~/shared/types/rooms";
import { getFeed } from "~/services/api/rooms";

const store = useRoomStore();

const feed = ref<FeedEvent[]>([]);
const cursor = ref<number | null>(null);
const done = ref(false);

async function load(more = false) {
  if (done.value && more) return;
  const events = await getFeed(store.roomId, {
    limit: 30,
    ...(more && cursor.value ? { cursor: cursor.value } : {}),
  });
  feed.value = more ? [...feed.value, ...events] : events;
  cursor.value = events.length
    ? events[events.length - 1]!.id
    : cursor.value;
  done.value = events.length < 30;
}

onMounted(() => load());

function feedText(event: FeedEvent): string {
  switch (event.type) {
    case "entry_completed":
      return `completed ${event.room_habit_name ?? "a habit"}`;
    case "member_joined":
      return "joined the room";
    case "member_left":
      return "left the room";
    case "habit_linked":
      return `linked a habit to ${event.room_habit_name ?? "a room habit"}`;
    case "room_habit_created":
      return `added room habit ${event.room_habit_name ?? ""}`;
    default:
      return event.type;
  }
}
</script>

<template>
  <div class="flex flex-col gap-2 pt-4">
    <p v-if="feed.length === 0" class="text-muted py-10 text-center text-sm">
      No activity yet.
    </p>
    <div
      v-for="event in feed"
      :key="event.id"
      class="flex items-center gap-3 py-1.5"
    >
      <UAvatar
        :src="event.photo_url ?? undefined"
        :alt="event.first_name"
        size="xs"
      />
      <p class="text-default flex-1 text-sm">
        <span class="font-medium">{{ event.first_name }}</span>
        {{ feedText(event) }}
      </p>
      <span class="text-dimmed text-xs tabular-nums">
        {{ new Date(event.created_at + "Z").toLocaleString() }}
      </span>
    </div>
    <UButton
      v-if="!done && feed.length > 0"
      label="Load more"
      variant="ghost"
      color="neutral"
      class="self-center"
      @click="load(true)"
    />
  </div>
</template>
