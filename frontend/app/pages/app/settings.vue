<script setup lang="ts">
import type { Preferences } from "~~/shared/types/api";
import { apiFetch, useAuthTokens } from "~/services/api/client";

definePageMeta({ layout: "dashboard" });
useHead({ title: "Settings" });

const toast = useToast();
const auth = useAuthStore();
const colorMode = useColorMode();
const { botUsername, apiBase } = useRuntimeConfig().public;

const prefs = ref<Preferences | null>(null);
const importing = ref(false);
const fileInput = ref<HTMLInputElement>();

const TIMEZONES = Intl.supportedValuesOf?.("timeZone") ?? ["UTC"];
const WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

onMounted(async () => {
  prefs.value = await apiFetch<Preferences>("/me/preferences");
  if (!prefs.value.timezone || prefs.value.timezone === "UTC") {
    const local = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (local && local !== prefs.value.timezone) {
      await save({ timezone: local });
    }
  }
});

async function save(patch: Partial<Preferences>) {
  try {
    prefs.value = await apiFetch<Preferences>("/me/preferences", { method: "PATCH", body: patch });
    if (patch.theme) colorMode.preference = patch.theme;
  } catch {
    toast.add({ title: "Could not save preferences", color: "error" });
  }
}

async function download(path: string, filename: string) {
  const { access } = useAuthTokens();
  try {
    const blob = await $fetch<Blob>(path, {
      baseURL: apiBase as string,
      responseType: "blob",
      headers: access.value ? { Authorization: `Bearer ${access.value}` } : {},
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  } catch {
    toast.add({ title: "Export failed", color: "error" });
  }
}

async function onImportFile(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  importing.value = true;
  try {
    const form = new FormData();
    form.append("file", file);
    const result = await apiFetch<{ habits_created: number; entries_imported: number }>(
      "/import/csv",
      { method: "POST", body: form },
    );
    toast.add({
      title: "Import complete",
      description: `${result.habits_created} habits created, ${result.entries_imported} entries imported.`,
      color: "success",
    });
  } catch {
    toast.add({ title: "Import failed", description: "Check the archive format.", color: "error" });
  } finally {
    importing.value = false;
    if (fileInput.value) fileInput.value.value = "";
  }
}

const botLink = computed(() => (botUsername ? `https://t.me/${botUsername}?start=link` : null));
</script>

<template>
  <UDashboardPanel id="settings">
    <template #header>
      <UDashboardNavbar title="Settings">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div v-if="prefs" class="mx-auto flex w-full max-w-2xl flex-col gap-6">
        <UCard>
          <template #header>
            <p class="font-semibold text-highlighted">Appearance & tracking</p>
          </template>
          <div class="flex flex-col gap-5">
            <UFormField label="Theme">
              <USelect
                :model-value="prefs.theme"
                :items="[
                  { label: 'System', value: 'system' },
                  { label: 'Light', value: 'light' },
                  { label: 'Dark', value: 'dark' },
                ]"
                class="w-40"
                @update:model-value="(v: any) => save({ theme: v })"
              />
            </UFormField>
            <UFormField label="First day of week">
              <USelect
                :model-value="prefs.first_weekday"
                :items="WEEKDAYS.map((label, value) => ({ label, value }))"
                class="w-40"
                @update:model-value="(v: any) => save({ first_weekday: v })"
              />
            </UFormField>
            <UFormField label="Timezone" hint="used for reminders and daily rollover">
              <USelectMenu
                :model-value="prefs.timezone"
                :items="TIMEZONES"
                class="w-64"
                @update:model-value="(v: any) => save({ timezone: v })"
              />
            </UFormField>
            <USwitch
              :model-value="prefs.skip_days_enabled"
              label="Skip days"
              description="Toggle cycle includes a Skip state that preserves streaks and scores."
              @update:model-value="(v: boolean) => save({ skip_days_enabled: v })"
            />
            <USwitch
              :model-value="prefs.show_question_marks"
              label="Question marks"
              description="Days without data show ? and can be explicitly marked as not done."
              @update:model-value="(v: boolean) => save({ show_question_marks: v })"
            />
          </div>
        </UCard>

        <UCard>
          <template #header>
            <p class="font-semibold text-highlighted">Telegram notifications</p>
          </template>
          <div class="flex flex-col gap-5">
            <div class="flex items-center justify-between gap-4">
              <div>
                <p class="text-sm font-medium text-default">Bot connection</p>
                <p class="text-sm text-muted">
                  {{ auth.user?.bot_linked ? "Connected — the bot can send you reminders." : "Connect the bot to receive reminders in Telegram." }}
                </p>
              </div>
              <UBadge v-if="auth.user?.bot_linked" color="success" variant="subtle" icon="i-lucide-check">
                Connected
              </UBadge>
              <UButton
                v-else-if="botLink"
                :to="botLink"
                target="_blank"
                icon="i-lucide-send"
                label="Connect bot"
              />
              <UBadge v-else color="neutral" variant="subtle">Bot not configured</UBadge>
            </div>
            <USwitch
              :model-value="prefs.reminders_enabled"
              label="Habit reminders"
              @update:model-value="(v: boolean) => save({ reminders_enabled: v })"
            />
            <USwitch
              :model-value="prefs.room_notifications"
              label="Room activity notifications"
              @update:model-value="(v: boolean) => save({ room_notifications: v })"
            />
          </div>
        </UCard>

        <UCard>
          <template #header>
            <p class="font-semibold text-highlighted">Data</p>
          </template>
          <div class="flex flex-col gap-4">
            <div class="flex flex-wrap gap-2">
              <UButton
                icon="i-lucide-download"
                label="Export CSV (Loop format)"
                variant="subtle"
                @click="download('/export/csv', 'habitflow-export.zip')"
              />
              <UButton
                icon="i-lucide-file-spreadsheet"
                label="Export Excel"
                variant="subtle"
                @click="download('/export/xlsx', 'habitflow-export.xlsx')"
              />
            </div>
            <div>
              <UButton
                icon="i-lucide-upload"
                :label="importing ? 'Importing…' : 'Import CSV archive'"
                :loading="importing"
                color="neutral"
                variant="subtle"
                @click="fileInput?.click()"
              />
              <input ref="fileInput" type="file" accept=".zip" class="hidden" @change="onImportFile" />
              <p class="mt-2 text-xs text-muted">
                Accepts HabitFlow / Loop CSV ZIP archives. Existing habits are matched by name.
              </p>
            </div>
          </div>
        </UCard>

        <UCard>
          <template #header>
            <p class="font-semibold text-highlighted">Account</p>
          </template>
          <div class="flex items-center justify-between gap-4">
            <p class="text-sm text-muted">Sign out of HabitFlow on this device.</p>
            <UButton
              icon="i-lucide-log-out"
              label="Log out"
              color="neutral"
              variant="subtle"
              @click="auth.logout()"
            />
          </div>
        </UCard>
      </div>
    </template>
  </UDashboardPanel>
</template>
