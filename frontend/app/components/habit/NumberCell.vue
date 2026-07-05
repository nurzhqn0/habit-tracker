<script setup lang="ts">
const props = defineProps<{
  value: number | undefined; // stored x1000
  targetValue: number;
  targetType: 0 | 1;
  color: string;
  unit: string;
}>();

const emit = defineEmits<{ save: [value: number] }>();

const open = ref(false);
const input = ref("");

const real = computed(() => (props.value !== undefined && props.value >= 0 ? props.value / 1000 : null));
const reached = computed(() => {
  if (real.value === null) return false;
  return props.targetType === 0 ? real.value >= props.targetValue : real.value <= props.targetValue;
});

function openPopover() {
  input.value = real.value !== null ? String(real.value) : "";
  open.value = true;
}

function save() {
  const parsed = Number(input.value);
  if (Number.isFinite(parsed) && parsed >= 0) {
    emit("save", Math.round(parsed * 1000));
    open.value = false;
  }
}
</script>

<template>
  <UPopover v-model:open="open">
    <button
      type="button"
      class="flex h-9 min-w-9 items-center justify-center rounded-md px-1 text-xs tabular-nums transition hover:bg-elevated"
      :class="reached ? 'font-bold' : 'text-dimmed'"
      :style="reached ? { color } : {}"
      @click="openPopover"
    >
      {{ real !== null ? real : "–" }}
    </button>

    <template #content>
      <form class="flex items-center gap-2 p-2" @submit.prevent="save">
        <UInput
          v-model="input"
          type="number"
          step="any"
          min="0"
          autofocus
          :placeholder="`0 ${unit}`"
          class="w-28"
        />
        <span v-if="unit" class="text-xs text-muted">{{ unit }}</span>
        <UButton type="submit" size="sm" icon="i-lucide-check" aria-label="Save" />
      </form>
    </template>
  </UPopover>
</template>
