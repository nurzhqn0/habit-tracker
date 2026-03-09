import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./App.css";
import { Card } from "./Card";
import { AddHabitModal } from "./AddHabitModal";
import Login from "./Login";

function Dashboard() {
  const [cards, setCards] = useState([
    { id: 1, emoji: "🚶", label: "Walk", goal: 10000, unit: "steps" },
    { id: 2, emoji: "💧", label: "Water", goal: 8, unit: "glasses" },
    { id: 3, emoji: "📚", label: "Read", goal: 30, unit: "minutes" },
  ]);
  const [openAddModal, setOpenAddModal] = useState(false);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-white gap-4">
      {cards.map((card) => (
        <Card
          key={card.id}
          emoji={card.emoji}
          label={card.label}
          goal={card.goal}
          unit={card.unit}
        />
      ))}

      <button
        onClick={() => setOpenAddModal(true)}
        className="px-6 py-3 rounded-xl font-semibold text-base hover:opacity-80"
        style={{ background: "#22c55e", color: "#000" }}
      >
        + Add Habit
      </button>

      {openAddModal && (
        <AddHabitModal
          closeModal={setOpenAddModal}
          onAdd={(newCard) => setCards((prev) => [...prev, newCard])}
        />
      )}
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
