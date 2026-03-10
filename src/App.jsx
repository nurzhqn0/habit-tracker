import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./App.css";
import { Card } from "./Card";
import { AddHabitModal } from "./AddHabitModal";
import Login from "./Login";

function Calendar() {
  const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  const today = new Date();
  const todayDate = today.getDate();
  const todayDay = today.getDay();

  const startOfWeek = new Date(today);
  startOfWeek.setDate(todayDate - todayDay);

  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(startOfWeek);
    d.setDate(startOfWeek.getDate() + i);
    return { name: dayNames[i], date: d.getDate(), isToday: i === todayDay };
  });

  const [selected, setSelected] = useState(todayDay);

  return (
    <div className="flex bg-white shadow-md justify-center rounded-xl py-4 px-2 gap-1 w-full max-w-md">
      {days.map((day, i) => {
        const isSelected = i === selected;
        return isSelected ? (
          <div
            key={i}
            onClick={() => setSelected(i)}
            className="flex bg-purple-600 shadow-lg rounded-full mx-1 cursor-pointer justify-center relative w-16"
          >
            <span className="flex h-2 w-2 absolute bottom-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-100"></span>
            </span>
            <div className="flex items-center px-4 my-2 py-4">
              <div className="text-center">
                <p className="text-gray-100 text-sm font-semibold">
                  {day.name}
                </p>
                <p className="text-gray-100 mt-3 font-bold">{day.date}</p>
              </div>
            </div>
          </div>
        ) : (
          <div
            key={i}
            onClick={() => setSelected(i)}
            className="flex group hover:bg-purple-500 hover:shadow-lg rounded-full mx-1 transition-all duration-300 cursor-pointer justify-center w-16"
          >
            <div className="flex items-center px-4 py-4">
              <div className="text-center">
                <p className="text-gray-900 group-hover:text-gray-100 text-sm transition-all duration-300">
                  {day.name}
                </p>
                <p className="text-gray-900 group-hover:text-gray-100 mt-3 group-hover:font-bold transition-all duration-300">
                  {day.date}
                </p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function Dashboard() {
  const [cards, setCards] = useState([
    { id: 1, emoji: "🚶", label: "Walk", goal: 10000, unit: "steps" },
    { id: 2, emoji: "💧", label: "Water", goal: 8, unit: "glasses" },
    { id: 3, emoji: "📚", label: "Read", goal: 30, unit: "minutes" },
  ]);
  const [openAddModal, setOpenAddModal] = useState(false);

  const today = new Date();
  const options = { weekday: "long", month: "long", day: "numeric" };
  const dateString = today.toLocaleDateString("en-US", options);

  return (
    <div className="flex flex-col items-center min-h-screen bg-white gap-4 px-4 py-8">
      {/* Calendar */}
      <Calendar />

      {/* Cards */}
      {cards.map((card) => (
        <Card
          key={card.id}
          emoji={card.emoji}
          label={card.label}
          goal={card.goal}
          unit={card.unit}
        />
      ))}

      {/* Add Habit Button */}
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
