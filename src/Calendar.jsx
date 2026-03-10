import { useState } from "react";
export default function Calendar() {
  const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  const today = new Date();
  const todayDate = today.getDate();
  const todayDay = today.getDay();

  const startOfWeek = new Date(today);
  startOfWeek.setDate(todayDate - todayDay);

  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(startOfWeek);
    d.setDate(startOfWeek.getDate() + i);
    return { name: dayNames[i], date: d.getDate() };
  });

  const [selected, setSelected] = useState(todayDay);

  return (
    <div
      className="flex justify-between rounded-2xl px-3 py-4 w-full max-w-md"
      style={{ background: "#1a1a1a" }}
    >
      {days.map((day, i) => {
        const isSelected = i === selected;
        const isToday = i === todayDay;
        return (
          <div
            key={i}
            onClick={() => setSelected(i)}
            className="flex flex-col items-center justify-center cursor-pointer rounded-full px-2 py-3 transition-all duration-300 w-11"
            style={{
              background: isSelected ? "#7c3aed" : "transparent",
              boxShadow: isSelected
                ? "0 4px 15px rgba(124,58,237,0.4)"
                : "none",
            }}
          >
            <p
              className="text-xs font-medium mb-2"
              style={{ color: isSelected ? "#e5e7eb" : "#6b7280" }}
            >
              {day.name}
            </p>
            <p
              className="text-sm font-bold"
              style={{ color: isSelected ? "#fff" : "#d1d5db" }}
            >
              {day.date}
            </p>
            {isToday && (
              <span
                className="mt-2 h-1.5 w-1.5 rounded-full"
                style={{ background: isSelected ? "#c4b5fd" : "#7c3aed" }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
