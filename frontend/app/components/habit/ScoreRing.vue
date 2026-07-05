<script setup lang="ts">
const props = withDefaults(
  defineProps<{ score: number; color: string; size?: number }>(),
  { size: 36 },
);

const radius = computed(() => props.size / 2 - 3);
const circumference = computed(() => 2 * Math.PI * radius.value);
const offset = computed(() => circumference.value * (1 - Math.min(1, Math.max(0, props.score))));
</script>

<template>
  <UTooltip :text="`Strength: ${Math.round(score * 100)}%`">
    <svg :width="size" :height="size" :viewBox="`0 0 ${size} ${size}`" class="shrink-0 -rotate-90">
      <circle
        :cx="size / 2" :cy="size / 2" :r="radius"
        fill="none" :stroke="color" stroke-opacity="0.25" stroke-width="4"
      />
      <circle
        :cx="size / 2" :cy="size / 2" :r="radius"
        fill="none" :stroke="color" stroke-width="4" stroke-linecap="round"
        :stroke-dasharray="circumference" :stroke-dashoffset="offset"
        class="transition-[stroke-dashoffset] duration-500"
      />
    </svg>
  </UTooltip>
</template>
