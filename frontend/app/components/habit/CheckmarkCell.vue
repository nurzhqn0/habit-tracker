<script setup lang="ts">
import { NO, SKIP, UNKNOWN, YES_AUTO, YES_MANUAL } from "~~/shared/types/habits";

const props = defineProps<{
  value: number | undefined;
  color: string;
  showQuestionMarks: boolean;
}>();

const emit = defineEmits<{ toggle: [] }>();

const display = computed(() => {
  const value = props.value ?? UNKNOWN;
  switch (value) {
    case YES_MANUAL:
      return { icon: "i-lucide-check", style: { color: props.color }, cls: "font-bold" };
    case YES_AUTO:
      return { icon: "i-lucide-check", style: { color: props.color, opacity: 0.45 }, cls: "" };
    case SKIP:
      return { icon: "i-lucide-fast-forward", style: { color: props.color }, cls: "" };
    case NO:
      return { icon: "i-lucide-x", style: {}, cls: "text-dimmed" };
    default:
      return props.showQuestionMarks
        ? { icon: "i-lucide-circle-help", style: {}, cls: "text-dimmed opacity-60" }
        : { icon: "i-lucide-x", style: {}, cls: "text-dimmed opacity-40" };
  }
});
</script>

<template>
  <button
    type="button"
    data-testid="check-cell"
    class="flex size-9 items-center justify-center rounded-md transition hover:bg-elevated active:scale-90"
    @click="emit('toggle')"
  >
    <UIcon :name="display.icon" class="size-5" :class="display.cls" :style="display.style" />
  </button>
</template>
