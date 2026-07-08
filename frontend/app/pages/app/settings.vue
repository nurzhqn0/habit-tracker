<script setup lang="ts">
import type { Preferences } from "~~/shared/types/api";
import { apiFetch } from "~/services/api/client";

definePageMeta({ layout: "dashboard" });
useHead({ title: "Settings" });

const toast = useToast();
const auth = useAuthStore();
const colorMode = useColorMode();
const { sendToTelegram, sending } = useDownload();

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
</script>

<template>
  <UDashboardPanel id="settings">
    <template #header>
      <UDashboardNavbar title="Settings" :toggle="false">
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
            <p class="font-semibold text-highlighted">Data</p>
          </template>
          <div class="flex flex-col gap-4">
            <div class="flex flex-wrap gap-2">
              <UButton
                icon="i-lucide-send"
                label="Export CSV (Loop format)"
                variant="subtle"
                :loading="sending"
                @click="sendToTelegram('/export/csv')"
              />
              <UButton
                icon="i-lucide-send"
                label="Export Excel"
                variant="subtle"
                :loading="sending"
                @click="sendToTelegram('/export/xlsx')"
              />
            </div>
            <p class="text-xs text-muted">Exports are delivered to your Telegram chat by the bot.</p>
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


      </div>
    </template>
  </UDashboardPanel>
</template>
