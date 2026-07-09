<script setup lang="ts">
defineProps<{
  label: string;
  value: number | null;
  icon: string;
}>();
</script>

<template>
  <UCard>
    <div class="flex items-center gap-3">
      <UIcon :name="icon" class="text-primary size-6 shrink-0" />
      <div>
        <p class="text-2xl font-bold tabular-nums">
          <template v-if="value !== null">{{ value }}</template>
          <USkeleton v-else class="h-8 w-12" />
        </p>
        <p class="text-muted text-xs">{{ label }}</p>
      </div>
    </div>
  </UCard>
</template>
