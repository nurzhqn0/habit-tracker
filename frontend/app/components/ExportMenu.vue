<script setup lang="ts">
import type { DateRange } from "reka-ui";
import { parseDate } from "@internationalized/date";
import { todayKey, shiftDateKey } from "~/composables/useDates";

const props = defineProps<{
  path: string;
  filenamePrefix: string;
}>();

const { download, downloading } = useDownload();
const open = ref(false);
const range = shallowRef<DateRange | null>(null);
const maxDate = parseDate(todayKey());

async function run(from: string, to: string) {
  open.value = false;
  await download(props.path, `${props.filenamePrefix}_${from}_${to}.xlsx`, { from, to });
}

function runRange() {
  if (!range.value?.start || !range.value?.end) return;
  run(range.value.start.toString(), range.value.end.toString());
}
</script>

<template>
  <UPopover v-model:open="open">
    <UButton
      icon="i-lucide-download"
      label="Export"
      color="neutral"
      variant="ghost"
      :loading="downloading"
      aria-label="Export"
      :ui="{ label: 'hidden sm:inline' }"
    />
    <template #content>
      <div class="flex w-72 flex-col gap-2 p-3">
        <UButton
          label="This week"
          variant="soft"
          block
          @click="run(shiftDateKey(todayKey(), -6), todayKey())"
        />
        <UButton
          label="This month (last 30 days)"
          variant="soft"
          block
          @click="run(shiftDateKey(todayKey(), -29), todayKey())"
        />
        <USeparator label="Custom range" />
        <UCalendar v-model="range" range :max-value="maxDate" size="sm" />
        <UButton
          label="Export range"
          block
          :disabled="!range?.start || !range?.end"
          @click="runRange"
        />
      </div>
    </template>
  </UPopover>
</template>
