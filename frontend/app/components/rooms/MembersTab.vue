<script setup lang="ts">
import type { DropdownMenuItem } from "@nuxt/ui";
import type { RoomMember } from "~~/shared/types/rooms";

const store = useRoomStore();
const auth = useAuthStore();
const view = useRoomViewStore();
const router = useRouter();
const toast = useToast();

function openMember(member: RoomMember) {
  view.viewedMember = member;
  navigateTo(`/app/rooms/${store.roomId}/members/${member.user_id}`);
}

async function removeMember(member: RoomMember) {
  try {
    await store.removeMember(member.user_id);
    if (member.user_id === auth.user?.id) router.replace("/app/rooms");
  } catch {
    toast.add({ title: "Could not remove member", color: "error" });
  }
}

async function setRole(member: RoomMember, role: "admin" | "member") {
  try {
    await store.setRole(member.user_id, role);
  } catch {
    toast.add({ title: "Could not change role", color: "error" });
  }
}

const transferFor = ref<RoomMember | null>(null);

async function transferOwnership() {
  if (!transferFor.value) return;
  try {
    await store.transferOwnership(transferFor.value.user_id);
    transferFor.value = null;
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
        onSelect: () => openMember(member),
      },
    ],
  ];
  if (store.isOwner && member.role !== "owner") {
    items.push([
      member.role === "admin"
        ? {
            label: "Demote to member",
            icon: "i-lucide-shield-off",
            onSelect: () => setRole(member, "member"),
          }
        : {
            label: "Promote to admin",
            icon: "i-lucide-shield",
            onSelect: () => setRole(member, "admin"),
          },
      {
        label: "Transfer ownership",
        icon: "i-lucide-crown",
        onSelect: () => (transferFor.value = member),
      },
    ]);
  }
  if ((store.isOwner || member.role === "member") && member.role !== "owner") {
    items.push([
      {
        label: "Remove from room",
        icon: "i-lucide-user-x",
        color: "error",
        onSelect: () => removeMember(member),
      },
    ]);
  }
  return items;
}
</script>

<template>
  <div class="flex flex-col gap-2 pt-4">
    <div
      v-for="member in store.members"
      :key="member.user_id"
      class="flex items-center gap-3 py-1.5"
      :class="store.isAdmin ? 'hover:bg-elevated/60 -mx-2 rounded-md px-2' : ''"
    >
      <div
        class="flex flex-1 items-center gap-3"
        :class="store.isAdmin ? 'cursor-pointer' : ''"
        @click="store.isAdmin && openMember(member)"
      >
        <UAvatar
          :src="member.photo_url ?? undefined"
          :alt="member.first_name"
          size="sm"
        />
        <div class="min-w-0">
          <p class="text-default text-sm font-medium">
            {{ member.first_name }}
          </p>
          <p class="text-muted text-xs">@{{ member.username ?? "—" }}</p>
        </div>
      </div>
      <UBadge
        v-if="member.role === 'owner'"
        variant="subtle"
        color="warning"
        icon="i-lucide-crown"
      >
        Owner
      </UBadge>
      <UBadge
        v-else-if="member.role === 'admin'"
        variant="subtle"
        color="info"
        icon="i-lucide-shield"
      >
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
        v-else-if="member.user_id !== auth.user?.id && store.isAdmin"
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

    <ConfirmModal
      :open="!!transferFor"
      :title="`Transfer ownership to ${transferFor?.first_name}?`"
      description="They become the room owner and you stay as an admin. This cannot be undone by you."
      confirm-label="Transfer ownership"
      confirm-color="warning"
      confirm-icon="i-lucide-crown"
      @update:open="transferFor = null"
      @confirm="transferOwnership"
    />
  </div>
</template>
