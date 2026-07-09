<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string;
    description?: string;
    confirmLabel: string;
    confirmColor?: "error" | "warning" | "primary";
    confirmIcon?: string;
  }>(),
  { confirmColor: "error" },
);

const open = defineModel<boolean>("open", { required: true });

const emit = defineEmits<{ confirm: [] }>();
</script>

<template>
  <UModal v-model:open="open" :title="title" :description="description">
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton
          label="Cancel"
          color="neutral"
          variant="ghost"
          @click="
            () => {
              open = false;
            }
          "
        />
        <UButton
          :label="confirmLabel"
          :color="confirmColor"
          :icon="confirmIcon"
          @click="emit('confirm')"
        />
      </div>
    </template>
  </UModal>
</template>
