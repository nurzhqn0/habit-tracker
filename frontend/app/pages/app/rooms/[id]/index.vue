<script setup lang="ts">
import type { DropdownMenuItem } from "@nuxt/ui";
import type { FeedEvent, LeaderboardRow, Room, RoomHabitWithLink, RoomMember } from "~~/shared/types/rooms";
import type { Habit } from "~~/shared/types/habits";
import { apiFetch } from "~/services/api/client";
import { paletteColor } from "~/composables/usePalette";

definePageMeta({ layout: "dashboard" });

const route = useRoute();
const router = useRouter();
const toast = useToast();
const auth = useAuthStore();
const roomId = Number(route.params.id);

const room = ref<Room | null>(null);
const habits = ref<RoomHabitWithLink[]>([]);
const members = ref<RoomMember[]>([]);
const leaderboard = ref<LeaderboardRow[]>([]);
const feed = ref<FeedEvent[]>([]);
const feedCursor = ref<number | null>(null);
const feedDone = ref(false);
const period = ref<"week" | "month" | "all">("week");
const loading = ref(true);

const isOwner = computed(() => room.value?.owner_id === auth.user?.id);
const myRole = computed(() => members.value.find((m) => m.user_id === auth.user?.id)?.role);
const isAdmin = computed(() => isOwner.value || myRole.value === "admin");

useHead({ title: computed(() => room.value?.name ?? "Room") });

const inviteOpen = ref(false);
const inviteLink = ref("");
const habitFormOpen = ref(false);
const newHabit = reactive({ name: "", type: 0 as 0 | 1, target_value: 0, unit: "", freq_num: 1, freq_den: 1 });
const linkPickerFor = ref<RoomHabitWithLink | null>(null);
const myHabits = ref<Habit[]>([]);
const busy = ref(false);

async function loadCore() {
  room.value = await apiFetch<Room>(`/rooms/${roomId}`);
  [habits.value, members.value] = await Promise.all([
    apiFetch<RoomHabitWithLink[]>(`/rooms/${roomId}/habits`),
    apiFetch<RoomMember[]>(`/rooms/${roomId}/members`),
  ]);
}

async function loadLeaderboard() {
  leaderboard.value = await apiFetch<LeaderboardRow[]>(`/rooms/${roomId}/leaderboard`, {
    query: { period: period.value },
  });
}

async function loadFeed(more = false) {
  if (feedDone.value && more) return;
  const events = await apiFetch<FeedEvent[]>(`/rooms/${roomId}/feed`, {
    query: { limit: 30, ...(more && feedCursor.value ? { cursor: feedCursor.value } : {}) },
  });
  feed.value = more ? [...feed.value, ...events] : events;
  feedCursor.value = events.length ? events[events.length - 1]!.id : feedCursor.value;
  feedDone.value = events.length < 30;
}

onMounted(async () => {
  try {
    await loadCore();
    await Promise.all([loadLeaderboard(), loadFeed()]);
  } catch {
    toast.add({ title: "Room not found", color: "error" });
    router.replace("/app/rooms");
  } finally {
    loading.value = false;
  }
});

watch(period, loadLeaderboard);

async function showInvite() {
  const result = await apiFetch<{ invite_code: string; link: string }>(
    `/rooms/${roomId}/invite/rotate`,
    { method: "POST" },
  );
  inviteLink.value = result.link;
  inviteUsername.value = "";
  inviteResult.value = null;
  inviteOpen.value = true;
}

interface InviteResult {
  status: "sent" | "not_linked" | "not_registered" | "already_member";
  username: string;
  link: string;
}

const inviteUsername = ref("");
const inviteBusy = ref(false);
const inviteResult = ref<InviteResult | null>(null);

async function sendUsernameInvite() {
  if (!inviteUsername.value.trim()) return;
  inviteBusy.value = true;
  try {
    inviteResult.value = await apiFetch<InviteResult>(`/rooms/${roomId}/invite`, {
      method: "POST",
      body: { username: inviteUsername.value },
    });
  } catch {
    toast.add({ title: "Could not send invite", color: "error" });
  } finally {
    inviteBusy.value = false;
  }
}

const inviteShareUrl = computed(() => {
  if (!inviteResult.value) return "";
  const text = `Join “${room.value?.name}” on HabitFlow!`;
  return `https://t.me/share/url?url=${encodeURIComponent(inviteResult.value.link)}&text=${encodeURIComponent(text)}`;
});

async function copyInvite() {
  await navigator.clipboard.writeText(inviteLink.value);
  toast.add({ title: "Invite link copied", color: "success" });
}

const editingHabitId = ref<number | null>(null);

function openHabitForm(item?: RoomHabitWithLink) {
  editingHabitId.value = item?.habit.id ?? null;
  newHabit.name = item?.habit.name ?? "";
  newHabit.type = item?.habit.type ?? 0;
  newHabit.target_value = item?.habit.target_value ?? 0;
  newHabit.unit = item?.habit.unit ?? "";
  newHabit.freq_num = item?.habit.freq_num ?? 1;
  newHabit.freq_den = item?.habit.freq_den ?? 1;
  habitFormOpen.value = true;
}

async function saveRoomHabit() {
  busy.value = true;
  try {
    if (editingHabitId.value) {
      const { type, ...fields } = newHabit;
      await apiFetch(`/rooms/${roomId}/habits/${editingHabitId.value}`, { method: "PATCH", body: fields });
    } else {
      await apiFetch(`/rooms/${roomId}/habits`, { method: "POST", body: { ...newHabit } });
    }
    habitFormOpen.value = false;
    newHabit.name = "";
    await loadCore();
  } catch {
    toast.add({ title: "Could not save room habit", color: "error" });
  } finally {
    busy.value = false;
  }
}

const deleteHabitFor = ref<RoomHabitWithLink | null>(null);

async function deleteRoomHabit() {
  if (!deleteHabitFor.value) return;
  try {
    await apiFetch(`/rooms/${roomId}/habits/${deleteHabitFor.value.habit.id}`, { method: "DELETE" });
    deleteHabitFor.value = null;
    await Promise.all([loadCore(), loadLeaderboard()]);
  } catch {
    toast.add({ title: "Could not delete room habit", color: "error" });
  }
}

async function openLinkPicker(item: RoomHabitWithLink) {
  linkPickerFor.value = item;
  // Only same-type habits not already linked to a habit in this room.
  const linkedIds = new Set(habits.value.map((h) => h.linked_habit_id).filter(Boolean));
  myHabits.value = (await apiFetch<Habit[]>("/habits", { query: { archived: false } })).filter(
    (h) => h.type === item.habit.type && !linkedIds.has(h.id),
  );
}

async function link(habitId: number | null) {
  if (!linkPickerFor.value) return;
  busy.value = true;
  try {
    await apiFetch(`/rooms/${roomId}/habits/${linkPickerFor.value.habit.id}/link`, {
      method: "POST",
      body: habitId ? { habit_id: habitId } : {},
    });
    linkPickerFor.value = null;
    await Promise.all([loadCore(), loadLeaderboard()]);
    toast.add({ title: "Habit linked", color: "success" });
  } catch (error: any) {
    const detail = error?.data?.detail ?? "Could not link habit";
    toast.add({ title: detail, color: "error" });
  } finally {
    busy.value = false;
  }
}

async function unlink(item: RoomHabitWithLink) {
  await apiFetch(`/rooms/${roomId}/habits/${item.habit.id}/link`, { method: "DELETE" });
  await Promise.all([loadCore(), loadLeaderboard()]);
}

async function removeMember(member: RoomMember) {
  try {
    await apiFetch(`/rooms/${roomId}/members/${member.user_id}`, { method: "DELETE" });
    if (member.user_id === auth.user?.id) {
      router.replace("/app/rooms");
      return;
    }
    await loadCore();
  } catch {
    toast.add({ title: "Could not remove member", color: "error" });
  }
}

async function setRole(member: RoomMember, role: "admin" | "member") {
  try {
    await apiFetch(`/rooms/${roomId}/members/${member.user_id}`, { method: "PATCH", body: { role } });
    await loadCore();
  } catch {
    toast.add({ title: "Could not change role", color: "error" });
  }
}

const transferFor = ref<RoomMember | null>(null);

async function transferOwnership() {
  if (!transferFor.value) return;
  try {
    await apiFetch(`/rooms/${roomId}/transfer-ownership`, {
      method: "POST",
      body: { user_id: transferFor.value.user_id },
    });
    transferFor.value = null;
    await loadCore();
    toast.add({ title: "Ownership transferred", color: "success" });
  } catch {
    toast.add({ title: "Could not transfer ownership", color: "error" });
  }
}

function memberMenu(member: RoomMember): DropdownMenuItem[][] {
  const items: DropdownMenuItem[][] = [
    [
      {
        label: "View habits",
        icon: "i-lucide-chart-line",
        to: `/app/rooms/${roomId}/members/${member.user_id}`,
      },
    ],
  ];
  if (isOwner.value && member.role !== "owner") {
    items.push([
      member.role === "admin"
        ? { label: "Demote to member", icon: "i-lucide-shield-off", onSelect: () => setRole(member, "member") }
        : { label: "Promote to admin", icon: "i-lucide-shield", onSelect: () => setRole(member, "admin") },
      { label: "Transfer ownership", icon: "i-lucide-crown", onSelect: () => (transferFor.value = member) },
    ]);
  }
  if ((isOwner.value || member.role === "member") && member.role !== "owner") {
    items.push([
      { label: "Remove from room", icon: "i-lucide-user-x", color: "error", onSelect: () => removeMember(member) },
    ]);
  }
  return items;
}

const deleteRoomOpen = ref(false);

async function deleteRoom() {
  deleteRoomOpen.value = false;
  await apiFetch(`/rooms/${roomId}`, { method: "DELETE" });
  router.replace("/app/rooms");
}

function linkTypeLabel(item: RoomHabitWithLink): string {
  if (item.habit.type !== 1) return "Yes / No";
  const direction = item.habit.target_type === 0 ? "at least" : "at most";
  return `Measurable · ${direction} ${item.habit.target_value} ${item.habit.unit}`.trim();
}

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

const tabs = [
  { label: "Habits", slot: "habits", icon: "i-lucide-list-checks" },
  { label: "Leaderboard", slot: "leaderboard", icon: "i-lucide-trophy" },
  { label: "Feed", slot: "feed", icon: "i-lucide-activity" },
  { label: "Members", slot: "members", icon: "i-lucide-users" },
];
</script>

<template>
  <UDashboardPanel id="room-detail">
    <template #header>
      <UDashboardNavbar :title="room?.name ?? 'Room'" :toggle="false">
        <template #leading>
          <UButton icon="i-lucide-arrow-left" color="neutral" variant="ghost" to="/app/rooms" aria-label="Back" />
        </template>
        <template #right>
          <UButton
            v-if="isAdmin"
            icon="i-lucide-user-plus"
            label="Invite"
            variant="subtle"
            @click="showInvite"
          />
          <UButton
            v-if="isOwner"
            icon="i-lucide-trash-2"
            color="error"
            variant="ghost"
            aria-label="Delete room"
            @click="deleteRoomOpen = true"
          />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div v-if="loading" class="flex justify-center py-16">
        <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin text-muted" />
      </div>

      <UTabs
        v-else
        :items="tabs"
        class="w-full"
        variant="link"
        :ui="{ list: 'overflow-x-auto', trigger: 'flex-none' }"
      >
        <template #habits>
          <div class="flex flex-col gap-3 pt-4">
            <div v-if="isAdmin" class="flex justify-end">
              <UButton icon="i-lucide-plus" label="Add room habit" size="sm" @click="openHabitForm()" />
            </div>

            <p v-if="habits.length === 0" class="py-10 text-center text-sm text-muted">
              No room habits yet.{{ isAdmin ? " Add one so members can link their habits." : "" }}
            </p>

            <UCard v-for="item in habits" :key="item.habit.id">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div class="flex items-center gap-3">
                  <span
                    class="size-3 shrink-0 rounded-full"
                    :style="{ backgroundColor: paletteColor(item.habit.color) }"
                  />
                  <div>
                    <p class="font-medium text-highlighted">{{ item.habit.name }}</p>
                    <p class="text-xs text-muted">
                      {{ item.members_linked }} member{{ item.members_linked === 1 ? "" : "s" }} linked
                      <template v-if="item.habit.type === 1">
                        · {{ item.habit.target_type === 0 ? "at least" : "at most" }}
                        {{ item.habit.target_value }} {{ item.habit.unit }}
                      </template>
                    </p>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <template v-if="item.linked_habit_id">
                    <UButton
                      :to="`/app/habits/${item.linked_habit_id}`"
                      size="sm"
                      variant="subtle"
                      icon="i-lucide-chart-line"
                      label="My habit"
                    />
                    <UButton
                      size="sm"
                      color="neutral"
                      variant="ghost"
                      icon="i-lucide-unlink"
                      aria-label="Unlink"
                      @click="unlink(item)"
                    />
                  </template>
                  <UButton
                    v-else
                    size="sm"
                    icon="i-lucide-link"
                    label="Link my habit"
                    @click="openLinkPicker(item)"
                  />
                  <template v-if="isAdmin">
                    <UButton
                      size="sm"
                      color="neutral"
                      variant="ghost"
                      icon="i-lucide-pencil"
                      aria-label="Edit room habit"
                      @click="openHabitForm(item)"
                    />
                    <UButton
                      size="sm"
                      color="error"
                      variant="ghost"
                      icon="i-lucide-trash-2"
                      aria-label="Delete room habit"
                      @click="deleteHabitFor = item"
                    />
                  </template>
                </div>
              </div>
            </UCard>
          </div>
        </template>

        <template #leaderboard>
          <div class="flex flex-col gap-3 pt-4">
            <div class="flex justify-end">
              <USelect v-model="period" :items="['week', 'month', 'all']" size="sm" class="w-28" />
            </div>
            <UCard>
              <ol class="flex flex-col divide-y divide-default">
                <li
                  v-for="(row, index) in leaderboard"
                  :key="row.user_id"
                  class="flex items-center gap-3 py-2.5"
                >
                  <span class="w-6 text-center font-bold" :class="index === 0 ? 'text-warning' : 'text-muted'">
                    {{ index + 1 }}
                  </span>
                  <UAvatar :src="row.photo_url ?? undefined" :alt="row.first_name" size="sm" />
                  <div class="min-w-0 flex-1">
                    <p class="truncate text-sm font-medium text-default">
                      {{ row.first_name }}
                      <span v-if="row.user_id === auth.user?.id" class="text-xs text-muted">(you)</span>
                    </p>
                    <p class="text-xs text-muted">{{ row.linked_habits }} linked habits</p>
                  </div>
                  <div class="flex items-center gap-4 text-sm tabular-nums">
                    <span class="flex items-center gap-1 text-muted">
                      <UIcon name="i-lucide-flame" class="size-4 text-warning" />{{ row.streak }}
                    </span>
                    <span class="text-muted">{{ row.completions }} done</span>
                    <span class="w-12 text-right font-semibold text-highlighted">
                      {{ Math.round(row.score * 100) }}%
                    </span>
                  </div>
                </li>
              </ol>
            </UCard>
          </div>
        </template>

        <template #feed>
          <div class="flex flex-col gap-2 pt-4">
            <p v-if="feed.length === 0" class="py-10 text-center text-sm text-muted">No activity yet.</p>
            <div v-for="event in feed" :key="event.id" class="flex items-center gap-3 py-1.5">
              <UAvatar :src="event.photo_url ?? undefined" :alt="event.first_name" size="xs" />
              <p class="flex-1 text-sm text-default">
                <span class="font-medium">{{ event.first_name }}</span>
                {{ feedText(event) }}
              </p>
              <span class="text-xs tabular-nums text-dimmed">
                {{ new Date(event.created_at + "Z").toLocaleString() }}
              </span>
            </div>
            <UButton
              v-if="!feedDone && feed.length > 0"
              label="Load more"
              variant="ghost"
              color="neutral"
              class="self-center"
              @click="loadFeed(true)"
            />
          </div>
        </template>

        <template #members>
          <div class="flex flex-col gap-2 pt-4">
            <div v-for="member in members" :key="member.user_id" class="flex items-center gap-3 py-1.5">
              <UAvatar :src="member.photo_url ?? undefined" :alt="member.first_name" size="sm" />
              <div class="flex-1">
                <p class="text-sm font-medium text-default">{{ member.first_name }}</p>
                <p class="text-xs text-muted">@{{ member.username ?? "—" }}</p>
              </div>
              <UBadge v-if="member.role === 'owner'" variant="subtle" color="warning" icon="i-lucide-crown">
                Owner
              </UBadge>
              <UBadge v-else-if="member.role === 'admin'" variant="subtle" color="info" icon="i-lucide-shield">
                Admin
              </UBadge>
              <UButton
                v-if="member.user_id === auth.user?.id && member.role !== 'owner'"
                size="xs"
                color="neutral"
                variant="ghost"
                label="Leave"
                @click="removeMember(member)"
              />
              <UDropdownMenu
                v-else-if="member.user_id !== auth.user?.id && isAdmin"
                :items="memberMenu(member)"
              >
                <UButton
                  size="xs"
                  color="neutral"
                  variant="ghost"
                  icon="i-lucide-ellipsis-vertical"
                  aria-label="Member menu"
                />
              </UDropdownMenu>
            </div>
          </div>
        </template>
      </UTabs>

      <UModal v-model:open="inviteOpen" title="Invite friends">
        <template #body>
          <p class="mb-3 text-sm text-muted">
            Share this link — it was just rotated, so older links no longer work.
          </p>
          <div class="flex gap-2">
            <UInput :model-value="inviteLink" readonly class="flex-1" />
            <UButton icon="i-lucide-copy" aria-label="Copy" @click="copyInvite" />
          </div>

          <USeparator label="or" class="my-4" />

          <p class="mb-3 text-sm text-muted">
            Invite by Telegram username — we'll message them if they use HabitFlow.
          </p>
          <form class="flex gap-2" @submit.prevent="sendUsernameInvite">
            <UInput v-model="inviteUsername" placeholder="@username" class="flex-1" />
            <UButton
              type="submit"
              :loading="inviteBusy"
              :disabled="!inviteUsername.trim()"
              label="Send"
            />
          </form>

          <UAlert
            v-if="inviteResult?.status === 'sent'"
            class="mt-3"
            color="success"
            variant="subtle"
            icon="i-lucide-send"
            :title="`Invite sent to @${inviteResult.username} via Telegram.`"
          />
          <UAlert
            v-else-if="inviteResult?.status === 'not_linked'"
            class="mt-3"
            color="warning"
            variant="subtle"
            icon="i-lucide-bot-off"
            :title="`@${inviteResult.username} hasn't connected the Telegram bot.`"
            description="Share the invite link above with them directly."
          />
          <UAlert
            v-else-if="inviteResult?.status === 'already_member'"
            class="mt-3"
            color="info"
            variant="subtle"
            icon="i-lucide-user-check"
            :title="`@${inviteResult.username} is already in this room.`"
          />
          <UAlert
            v-else-if="inviteResult?.status === 'not_registered'"
            class="mt-3"
            color="info"
            variant="subtle"
            icon="i-lucide-user-plus"
            :title="`@${inviteResult.username} isn't on HabitFlow yet.`"
            description="Send them the invite link on Telegram — the room link doubles as an app invite."
          >
            <template #actions>
              <UButton
                :href="inviteShareUrl"
                target="_blank"
                size="xs"
                icon="i-lucide-send"
                label="Share on Telegram"
              />
              <UButton
                :href="`https://t.me/${inviteResult.username}`"
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

      <UModal v-model:open="habitFormOpen" :title="editingHabitId ? 'Edit room habit' : 'Add room habit'">
        <template #body>
          <form class="flex flex-col gap-4" @submit.prevent="saveRoomHabit">
            <UFormField label="Name" required>
              <UInput v-model="newHabit.name" class="w-full" autofocus />
            </UFormField>
            <UFormField v-if="!editingHabitId" label="Type">
              <URadioGroup
                v-model="newHabit.type"
                orientation="horizontal"
                :items="[
                  { label: 'Yes / No', value: 0 },
                  { label: 'Measurable', value: 1 },
                ]"
              />
            </UFormField>
            <div v-if="newHabit.type === 1" class="grid grid-cols-2 gap-3">
              <UFormField label="Daily target">
                <UInputNumber v-model="newHabit.target_value" :min="0" :step="0.5" />
              </UFormField>
              <UFormField label="Unit">
                <UInput v-model="newHabit.unit" placeholder="pages" />
              </UFormField>
            </div>
          </form>
        </template>
        <template #footer>
          <div class="flex w-full justify-end gap-2">
            <UButton color="neutral" variant="ghost" label="Cancel" @click="habitFormOpen = false" />
            <UButton
              :loading="busy"
              :disabled="!newHabit.name.trim()"
              :label="editingHabitId ? 'Save' : 'Add'"
              @click="saveRoomHabit"
            />
          </div>
        </template>
      </UModal>

      <UModal
        :open="!!transferFor"
        :title="`Transfer ownership to ${transferFor?.first_name}?`"
        description="They become the room owner and you stay as an admin. This cannot be undone by you."
        @update:open="transferFor = null"
      >
        <template #footer>
          <div class="flex w-full justify-end gap-2">
            <UButton label="Cancel" color="neutral" variant="ghost" @click="transferFor = null" />
            <UButton label="Transfer ownership" color="warning" icon="i-lucide-crown" @click="transferOwnership" />
          </div>
        </template>
      </UModal>

      <UModal
        :open="!!deleteHabitFor"
        :title="`Delete “${deleteHabitFor?.habit.name}”?`"
        description="Members' personal habits are kept, but unlinked from this room."
        @update:open="deleteHabitFor = null"
      >
        <template #footer>
          <div class="flex w-full justify-end gap-2">
            <UButton label="Cancel" color="neutral" variant="ghost" @click="deleteHabitFor = null" />
            <UButton label="Delete habit" color="error" icon="i-lucide-trash-2" @click="deleteRoomHabit" />
          </div>
        </template>
      </UModal>

      <UModal
        :open="!!linkPickerFor"
        :title="`Link a habit to “${linkPickerFor?.habit.name}”`"
        @update:open="linkPickerFor = null"
      >
        <template #body>
          <div class="flex flex-col gap-3">
            <UBadge v-if="linkPickerFor" variant="subtle" color="neutral" class="self-start">
              {{ linkTypeLabel(linkPickerFor) }}
            </UBadge>

            <UButton
              icon="i-lucide-plus"
              :label="`Create “${linkPickerFor?.habit.name}” from template`"
              variant="subtle"
              block
              :loading="busy"
              @click="link(null)"
            />

            <template v-if="myHabits.length">
              <p class="text-xs uppercase tracking-wide text-dimmed">or link an existing habit</p>
              <UButton
                v-for="habit in myHabits"
                :key="habit.id"
                color="neutral"
                variant="outline"
                block
                :loading="busy"
                @click="link(habit.id)"
              >
                <span
                  class="size-2.5 shrink-0 rounded-full"
                  :style="{ backgroundColor: paletteColor(habit.color) }"
                />
                <span class="truncate">{{ habit.name }}</span>
              </UButton>
            </template>
            <p v-else class="text-xs text-muted">
              No compatible habits to link — create one from the template above.
            </p>
          </div>
        </template>
      </UModal>

      <UModal
        v-model:open="deleteRoomOpen"
        :title="`Delete “${room?.name}”?`"
        description="The room, its habits and feed will be removed for every member. This cannot be undone."
      >
        <template #footer>
          <div class="flex w-full justify-end gap-2">
            <UButton label="Cancel" color="neutral" variant="ghost" @click="deleteRoomOpen = false" />
            <UButton label="Delete room" color="error" icon="i-lucide-trash-2" @click="deleteRoom" />
          </div>
        </template>
      </UModal>
    </template>
  </UDashboardPanel>
</template>
