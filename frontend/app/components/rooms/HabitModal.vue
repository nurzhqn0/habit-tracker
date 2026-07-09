<script setup lang="ts">
import type { RoomHabitWithLink } from "~~/shared/types/rooms";

const props = defineProps<{ item?: RoomHabitWithLink | null }>();

const open = defineModel<boolean>("open", { required: true });

const store = useRoomStore();
const toast = useToast();

const editingId = computed(() => props.item?.habit.id ?? null);
const busy = ref(false);
const form = reactive({
  name: "",
  type: 0 as 0 | 1,
  target_value: 0,
  unit: "",
  freq_num: 1,
  freq_den: 1,
});

watch(open, (value) => {
  if (!value) return;
  form.name = props.item?.habit.name ?? "";
  form.type = props.item?.habit.type ?? 0;
  form.target_value = props.item?.habit.target_value ?? 0;
  form.unit = props.item?.habit.unit ?? "";
  form.freq_num = props.item?.habit.freq_num ?? 1;
  form.freq_den = props.item?.habit.freq_den ?? 1;
});

async function save() {
  busy.value = true;
  try {
    await store.saveHabit({ ...form }, editingId.value);
    open.value = false;
  } catch {
    toast.add({ title: "Could not save room habit", color: "error" });
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <UModal
    v-model:open="open"
    :title="editingId ? 'Edit room habit' : 'Add room habit'"
  >
    <template #body>
      <form class="flex flex-col gap-4" @submit.prevent="save">
        <UFormField label="Name" required>
          <UInput v-model="form.name" class="w-full" autofocus />
        </UFormField>
        <UFormField v-if="!editingId" label="Type">
          <URadioGroup
            v-model="form.type"
            orientation="horizontal"
            :items="[
              { label: 'Yes / No', value: 0 },
              { label: 'Measurable', value: 1 },
            ]"
          />
        </UFormField>
        <div v-if="form.type === 1" class="grid grid-cols-2 gap-3">
          <UFormField label="Daily target">
            <UInputNumber v-model="form.target_value" :min="0" :step="0.5" />
          </UFormField>
          <UFormField label="Unit">
            <UInput v-model="form.unit" placeholder="pages" />
          </UFormField>
        </div>
      </form>
    </template>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton
          color="neutral"
          variant="ghost"
          label="Cancel"
          @click="
            () => {
              open = false;
            }
          "
        />
        <UButton
          :loading="busy"
          :disabled="!form.name.trim()"
          :label="editingId ? 'Save' : 'Add'"
          @click="save"
        />
      </div>
    </template>
  </UModal>
</template>
