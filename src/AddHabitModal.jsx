import { useState } from "react";

export function AddHabitModal({ closeModal, onAdd }) {
  const [emoji, setEmoji] = useState("");
  const [label, setLabel] = useState("");
  const [goal, setGoal] = useState("");
  const [unit, setUnit] = useState("");

  function handleAdd() {
    if (!label || !goal || !unit) return;
    onAdd({
      id: Date.now(),
      emoji,
      label,
      goal: Number(goal),
      unit,
    });
    closeModal(false);
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div
        className="p-6 rounded-2xl flex flex-col gap-4"
        style={{
          background: "#1e2330",
          width: "340px",
          boxShadow: "0 8px 40px rgba(0,0,0,0.6)",
        }}
      >
        <p className="text-white font-bold text-xl">New Habit</p>
        <input
          type="text"
          value={emoji}
          onChange={(e) => setEmoji(e.target.value)}
          placeholder="Emoji(e.g. 💪)"
          className="w-full px-4 py-3 rounded-xl text-white outline-none text-base"
          style={{ background: "#2a3147", border: "1px solid #3a4160" }}
        />
        <input
          type="text"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder="Habit name (e.g. Workout)"
          className="w-full px-4 py-3 rounded-xl text-white outline-none text-base"
          style={{ background: "#2a3147", border: "1px solid #3a4160" }}
        />
        <input
          type="number"
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="Goal (e.g 60)"
          className="w-full px-4 py-3 rounded-xl text-white outline-none text-base"
          style={{ background: "#2a3147", border: "1px solid #3a4160" }}
        />
        <input
          type="text"
          value={unit}
          onChange={(e) => setUnit(e.target.value)}
          placeholder="Unit (e.g. minutes)"
          className="w-full px-4 py-3 rounded-xl text-white outline-none text-base"
          style={{ background: "#2a3147", border: "1px solid #3a4160" }}
        />
        <div>
          <button
            onClick={() => closeModal(false)}
            className="w-full py-3 rounded-xl text-white font-semibold text-base hover:opacity-80"
            style={{ background: "#2e3650" }}
          >
            Cancel
          </button>
          <button
            onClick={handleAdd}
            className="w-full py-3 rounded-xl font-bold text-base hover:opacity-80 my-4"
            style={{ background: "#22c55e", color: "#000" }}
          >
            Create Habit
          </button>
        </div>
      </div>
    </div>
  );
}
