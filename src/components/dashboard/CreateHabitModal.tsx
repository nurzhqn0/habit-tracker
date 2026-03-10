"use client";

import { Button, Dialog, Flex, Select, Text, TextField } from "@radix-ui/themes";
import { FormEvent, useMemo, useState } from "react";
import { todayKey } from "../../lib/habit-utils";
import type { HabitUnit, NewHabitInput } from "../../types/habit";

type CreateHabitModalProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreateHabit: (input: NewHabitInput) => void;
};

const unitLabels: Record<HabitUnit, string> = {
  boolean: "True / False",
  liters: "Water (L)",
  pages: "Book pages",
  minutes: "Minutes",
};

export default function CreateHabitModal({ open, onOpenChange, onCreateHabit }: CreateHabitModalProps) {
  const [name, setName] = useState("");
  const [startDate, setStartDate] = useState(todayKey());
  const [unit, setUnit] = useState<HabitUnit>("boolean");
  const [target, setTarget] = useState("1");

  const canSubmit = useMemo(() => {
    if (!name.trim()) {
      return false;
    }

    if (unit === "boolean") {
      return true;
    }

    return Number(target) > 0;
  }, [name, target, unit]);

  const resetForm = () => {
    setName("");
    setStartDate(todayKey());
    setUnit("boolean");
    setTarget("1");
  };

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }

    onCreateHabit({
      name: name.trim(),
      startDate,
      unit,
      target: unit === "boolean" ? null : Number(target),
    });
    onOpenChange(false);
    resetForm();
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Content maxWidth="460px">
        <Dialog.Title>Create habit</Dialog.Title>
        <Dialog.Description size="2" mb="4">
          Add a new habit. You can track completion by day and view streaks in details.
        </Dialog.Description>

        <form onSubmit={onSubmit} className="grid gap-3">
          <label className="grid gap-1">
            <Text size="2" weight="medium">
              Habit name
            </Text>
            <TextField.Root
              placeholder="e.g. Drink water"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </label>

          <label className="grid gap-1">
            <Text size="2" weight="medium">
              Start date
            </Text>
            <TextField.Root type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
          </label>

          <label className="grid gap-1">
            <Text size="2" weight="medium">
              Unit
            </Text>
            <Select.Root value={unit} onValueChange={(value) => setUnit(value as HabitUnit)}>
              <Select.Trigger />
              <Select.Content>
                <Select.Item value="boolean">{unitLabels.boolean}</Select.Item>
                <Select.Item value="liters">{unitLabels.liters}</Select.Item>
                <Select.Item value="pages">{unitLabels.pages}</Select.Item>
                <Select.Item value="minutes">{unitLabels.minutes}</Select.Item>
              </Select.Content>
            </Select.Root>
          </label>

          {unit !== "boolean" ? (
            <label className="grid gap-1">
              <Text size="2" weight="medium">
                Daily target ({unitLabels[unit]})
              </Text>
              <TextField.Root
                type="number"
                min="1"
                step={unit === "liters" ? "0.1" : "1"}
                value={target}
                onChange={(event) => setTarget(event.target.value)}
              />
            </label>
          ) : (
            <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-3 py-2 text-xs text-slate-500">
              This habit uses done/not done tracking.
            </div>
          )}

          <Flex justify="end" gap="2" mt="3">
            <Button type="button" variant="soft" color="gray" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={!canSubmit}>
              Create
            </Button>
          </Flex>
        </form>
      </Dialog.Content>
    </Dialog.Root>
  );
}
