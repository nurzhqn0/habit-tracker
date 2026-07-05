<script setup lang="ts">
import type { Habit, HabitForm } from "~~/shared/types/habits";
import { PALETTE } from "~/composables/usePalette";

const props = defineProps<{ habit?: Habit }>();
const emit = defineEmits<{ saved: [] }>();

const open = defineModel<boolean>("open", { default: false });

const store = useHabitsStore();
const toast = useToast();
const saving = ref(false);

const isEdit = computed(() => !!props.habit);

const FREQ_PRESETS = [
  { label: "Every day", num: 1, den: 1 },
  { label: "Every week", num: 1, den: 7 },
  { label: "2 times per week", num: 2, den: 7 },
  { label: "3 times per week", num: 3, den: 7 },
  { label: "Every month", num: 1, den: 30 },
  { label: "Custom…", num: 0, den: 0 },
];

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
// uhabits weekday mask bit order: bit 0 = Saturday … bit 6 = Sunday (WeekdayList).
// We keep a simpler convention: bit i = WEEKDAYS[i] (Mon=bit0), used consistently by the bot.

function emptyForm(): HabitForm {
  return {
    name: "",
    question: "",
    description: "",
    type: 0,
    color: 8,
    freq_num: 1,
    freq_den: 1,
    reminder_hour: null,
    reminder_min: null,
    reminder_days: 127,
    target_type: 0,
    target_value: 0,
    unit: "",
  };
}

const form = reactive<HabitForm>(emptyForm());
const freqPreset = ref("Every day");
const customNum = ref(1);
const customDen = ref(7);
const reminderEnabled = ref(false);
const reminderTime = ref("09:00");

watch(open, (isOpen) => {
  if (!isOpen) return;
  if (props.habit) {
    Object.assign(form, {
      name: props.habit.name,
      question: props.habit.question,
      description: props.habit.description,
      type: props.habit.type,
      color: props.habit.color,
      freq_num: props.habit.freq_num,
      freq_den: props.habit.freq_den,
      reminder_hour: props.habit.reminder_hour,
      reminder_min: props.habit.reminder_min,
      reminder_days: props.habit.reminder_days,
      target_type: props.habit.target_type,
      target_value: props.habit.target_value,
      unit: props.habit.unit,
    });
    const preset = FREQ_PRESETS.find((p) => p.num === form.freq_num && p.den === form.freq_den);
    freqPreset.value = preset?.label ?? "Custom…";
    customNum.value = form.freq_num;
    customDen.value = form.freq_den;
    reminderEnabled.value = props.habit.reminder_hour !== null;
    if (props.habit.reminder_hour !== null) {
      reminderTime.value = `${String(props.habit.reminder_hour).padStart(2, "0")}:${String(
        props.habit.reminder_min ?? 0,
      ).padStart(2, "0")}`;
    }
  } else {
    Object.assign(form, emptyForm());
    freqPreset.value = "Every day";
    reminderEnabled.value = false;
    reminderTime.value = "09:00";
  }
});

function toggleReminderDay(index: number) {
  form.reminder_days ^= 1 << index;
}

const canSubmit = computed(() => {
  if (!form.name.trim()) return false;
  if (form.type === 1 && form.target_value <= 0) return false;
  return true;
});

async function submit() {
  const preset = FREQ_PRESETS.find((p) => p.label === freqPreset.value);
  if (preset && preset.num > 0) {
    form.freq_num = preset.num;
    form.freq_den = preset.den;
  } else {
    form.freq_num = Math.max(1, customNum.value);
    form.freq_den = Math.max(1, customDen.value);
  }

  if (reminderEnabled.value) {
    const [hour, minute] = reminderTime.value.split(":").map(Number);
    form.reminder_hour = hour ?? 9;
    form.reminder_min = minute ?? 0;
  } else {
    form.reminder_hour = null;
    form.reminder_min = null;
  }

  saving.value = true;
  try {
    if (isEdit.value && props.habit) {
      const body: Record<string, unknown> = { ...form };
      if (!reminderEnabled.value) {
        delete body.reminder_hour;
        delete body.reminder_min;
        body.clear_reminder = true;
      }
      await store.updateHabit(props.habit.id, body);
    } else {
      await store.createHabit({ ...form });
    }
    open.value = false;
    emit("saved");
  } catch {
    toast.add({ title: "Could not save habit", color: "error" });
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <UModal v-model:open="open" :title="isEdit ? 'Edit habit' : 'Create habit'">
    <template #body>
      <form class="flex flex-col gap-4" @submit.prevent="submit">
        <UFormField label="Name" required>
          <UInput v-model="form.name" placeholder="e.g. Meditate" class="w-full" autofocus />
        </UFormField>

        <UFormField label="Question" hint="shown on reminders">
          <UInput v-model="form.question" placeholder="e.g. Did you meditate today?" class="w-full" />
        </UFormField>

        <UFormField v-if="!isEdit" label="Type">
          <URadioGroup
            v-model="form.type"
            orientation="horizontal"
            :items="[
              { label: 'Yes / No', value: 0 },
              { label: 'Measurable', value: 1 },
            ]"
          />
        </UFormField>

        <UFormField label="Color">
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="(hex, index) in PALETTE"
              :key="hex"
              type="button"
              class="size-7 rounded-full transition hover:scale-110"
              :style="{ backgroundColor: hex }"
              :class="form.color === index ? 'ring-2 ring-offset-2 ring-primary ring-offset-[var(--ui-bg)]' : ''"
              :aria-label="`Color ${index + 1}`"
              @click="form.color = index"
            />
          </div>
        </UFormField>

        <UFormField label="Frequency">
          <USelect v-model="freqPreset" :items="FREQ_PRESETS.map((p) => p.label)" class="w-full" />
          <div v-if="freqPreset === 'Custom…'" class="mt-2 flex items-center gap-2 text-sm text-muted">
            <UInputNumber v-model="customNum" :min="1" :max="366" class="w-24" />
            <span>times per</span>
            <UInputNumber v-model="customDen" :min="1" :max="366" class="w-24" />
            <span>days</span>
          </div>
        </UFormField>

        <template v-if="form.type === 1">
          <div class="grid grid-cols-3 gap-3">
            <UFormField label="Target" required>
              <UInputNumber v-model="form.target_value" :min="0" :step="0.5" />
            </UFormField>
            <UFormField label="Unit">
              <UInput v-model="form.unit" placeholder="pages" />
            </UFormField>
            <UFormField label="Goal">
              <USelect
                v-model="form.target_type"
                :items="[
                  { label: 'At least', value: 0 },
                  { label: 'At most', value: 1 },
                ]"
              />
            </UFormField>
          </div>
        </template>

        <UFormField label="Reminder" hint="sent by the Telegram bot">
          <div class="flex flex-col gap-2">
            <div class="flex items-center gap-3">
              <USwitch v-model="reminderEnabled" />
              <UInput v-if="reminderEnabled" v-model="reminderTime" type="time" class="w-32" />
            </div>
            <div v-if="reminderEnabled" class="flex gap-1">
              <UButton
                v-for="(label, index) in WEEKDAYS"
                :key="label"
                size="xs"
                :variant="(form.reminder_days >> index) & 1 ? 'solid' : 'outline'"
                :color="(form.reminder_days >> index) & 1 ? 'primary' : 'neutral'"
                :label="label"
                @click="toggleReminderDay(index)"
              />
            </div>
          </div>
        </UFormField>

        <UFormField label="Notes">
          <UTextarea v-model="form.description" :rows="2" class="w-full" />
        </UFormField>
      </form>
    </template>

    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton color="neutral" variant="ghost" label="Cancel" @click="open = false" />
        <UButton
          :loading="saving"
          :disabled="!canSubmit"
          :label="isEdit ? 'Save' : 'Create'"
          @click="submit"
        />
      </div>
    </template>
  </UModal>
</template>
