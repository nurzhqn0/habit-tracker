<script setup lang="ts">
const open = defineModel<boolean>("open", { required: true });

const store = useRoomStore();
const toast = useToast();

const busy = ref(false);
const form = reactive({
  name: "",
  description: "",
  show_leaderboard: true,
  show_members: true,
});

watch(open, (value) => {
  if (!value || !store.room) return;
  form.name = store.room.name;
  form.description = store.room.description;
  form.show_leaderboard = store.room.show_leaderboard;
  form.show_members = store.room.show_members;
});

async function save() {
  busy.value = true;
  try {
    await store.updateRoom({ ...form });
    open.value = false;
    toast.add({ title: "Room settings saved", color: "success" });
  } catch {
    toast.add({ title: "Could not save room settings", color: "error" });
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <UModal v-model:open="open" title="Room settings">
    <template #body>
      <form class="flex flex-col gap-4" @submit.prevent="save">
        <UFormField label="Name" required>
          <UInput v-model="form.name" class="w-full" />
        </UFormField>
        <UFormField label="Description">
          <UTextarea v-model="form.description" class="w-full" :rows="3" />
        </UFormField>
        <USwitch
          v-model="form.show_leaderboard"
          label="Show leaderboard to members"
          description="Admins always see it."
        />
        <USwitch
          v-model="form.show_members"
          label="Show member list to members"
          description="Admins always see it."
        />
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
          label="Save"
          @click="save"
        />
      </div>
    </template>
  </UModal>
</template>
