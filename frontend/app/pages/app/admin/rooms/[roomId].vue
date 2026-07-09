<script setup lang="ts">
import type { AdminRoomDetail } from "~~/shared/types/admin";
import { getAdminRoom } from "~/services/api/admin";
import { paletteColor } from "~/composables/usePalette";

definePageMeta({ layout: "dashboard", middleware: "admin" });

const route = useRoute();
const router = useRouter();
const toast = useToast();
const roomId = Number(route.params.roomId);

const detail = ref<AdminRoomDetail | null>(null);
const loading = ref(true);

const title = computed(() => detail.value?.room.name ?? "Room");
useHead({ title });

onMounted(async () => {
  try {
    detail.value = await getAdminRoom(roomId);
  } catch {
    toast.add({ title: "Could not load room", color: "error" });
    router.replace("/app/admin");
    return;
  }
  loading.value = false;
});
</script>

<template>
  <UDashboardPanel id="admin-room">
    <template #header>
      <UDashboardNavbar :toggle="false">
        <template #leading>
          <UButton
            icon="i-lucide-arrow-left"
            color="neutral"
            variant="ghost"
            to="/app/admin"
            aria-label="Back"
          />
        </template>
        <template #title>
          <span v-if="detail">{{ detail.room.name }}</span>
          <USkeleton v-else class="h-5 w-36" />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div v-if="loading" class="flex justify-center py-16">
        <UIcon
          name="i-lucide-loader-circle"
          class="text-muted size-6 animate-spin"
        />
      </div>

      <div v-else-if="detail" class="flex flex-col gap-6">
        <UCard>
          <div class="flex flex-col gap-2">
            <p class="text-highlighted font-semibold">{{ detail.room.name }}</p>
            <p
              v-if="detail.room.description"
              class="text-muted text-sm whitespace-pre-line"
            >
              {{ detail.room.description }}
            </p>
            <div class="text-muted flex flex-wrap gap-x-4 gap-y-1 text-xs">
              <span>
                created
                {{ new Date(detail.room.created_at).toLocaleDateString() }}
              </span>
              <span class="font-mono">code: {{ detail.room.invite_code }}</span>
            </div>
          </div>
        </UCard>

        <section>
          <h3 class="text-highlighted mb-2 text-sm font-semibold">Owner</h3>
          <NuxtLink
            :to="`/app/admin/users/${detail.owner.id}`"
            class="hover:bg-elevated/50 flex items-center gap-3 rounded-md px-2 py-2 transition"
          >
            <UAvatar
              :src="detail.owner.photo_url ?? undefined"
              :alt="detail.owner.first_name"
              size="sm"
            />
            <div class="min-w-0 flex-1">
              <p class="text-highlighted truncate text-sm font-medium">
                {{ detail.owner.first_name }}
              </p>
              <p v-if="detail.owner.username" class="text-muted truncate text-xs">
                @{{ detail.owner.username }}
              </p>
            </div>
            <UIcon name="i-lucide-chevron-right" class="text-muted size-4" />
          </NuxtLink>
        </section>

        <section>
          <h3 class="text-highlighted mb-2 text-sm font-semibold">
            Members ({{ detail.members.length }})
          </h3>
          <div class="flex flex-col divide-y divide-default">
            <NuxtLink
              v-for="member in detail.members"
              :key="member.user_id"
              :to="`/app/admin/users/${member.user_id}`"
              class="hover:bg-elevated/50 flex items-center gap-3 px-2 py-2 transition"
            >
              <UAvatar
                :src="member.photo_url ?? undefined"
                :alt="member.first_name"
                size="sm"
              />
              <div class="min-w-0 flex-1">
                <p class="text-highlighted truncate text-sm font-medium">
                  {{ member.first_name }}
                </p>
                <p v-if="member.username" class="text-muted truncate text-xs">
                  @{{ member.username }}
                </p>
              </div>
              <UBadge :label="member.role" variant="subtle" size="sm" />
              <span class="text-muted text-xs tabular-nums">
                {{ new Date(member.joined_at).toLocaleDateString() }}
              </span>
            </NuxtLink>
          </div>
        </section>

        <section>
          <h3 class="text-highlighted mb-2 text-sm font-semibold">
            Room habits ({{ detail.habits.length }})
          </h3>
          <p
            v-if="detail.habits.length === 0"
            class="text-muted px-2 text-sm"
          >
            No habits in this room.
          </p>
          <div v-else class="flex flex-col divide-y divide-default">
            <div
              v-for="habit in detail.habits"
              :key="habit.id"
              class="flex items-center gap-3 px-2 py-2"
            >
              <span
                class="size-3 shrink-0 rounded-full"
                :style="{ backgroundColor: paletteColor(habit.color) }"
              />
              <div class="min-w-0 flex-1">
                <p class="text-highlighted truncate text-sm font-medium">
                  {{ habit.name }}
                </p>
                <p v-if="habit.description" class="text-muted truncate text-xs">
                  {{ habit.description }}
                </p>
              </div>
              <span class="text-muted text-xs tabular-nums">
                {{ habit.freq_num }}/{{ habit.freq_den }}d
                <template v-if="habit.type === 1">
                  · {{ habit.target_value }} {{ habit.unit }}
                </template>
              </span>
            </div>
          </div>
        </section>
      </div>
    </template>
  </UDashboardPanel>
</template>
