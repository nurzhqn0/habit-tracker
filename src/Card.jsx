import { useState } from "react";
import { Modal } from "./Modal";

export function Card({ emoji, label, goal, unit }) {
  const [current, setCurrent] = useState(0);
  const [openModel, setOpenModel] = useState(false);
  const progress = Math.min((current / goal) * 100, 100);
  const isComplete = current >= goal;

  return (
    <div>
      <div
        className="relative overflow-hidden rounded-2xl p-4"
        style={{
          background: "#1a1a1a",
          width: "360px",
          boxShadow: "0 4px 24px rgba(0,0,0,0.5)",
        }}
      >
        {/* Top row */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{emoji}</span>
            <div>
              <p className="text-white font-semibold text-lg leading-tight">
                {label}
              </p>
              <p className="text-gray-400 text-sm">
                {current.toLocaleString()}/{goal.toLocaleString()}
                {unit} {isComplete ? "🔥" : ""}
              </p>
            </div>
          </div>

          {/* + button */}

          <button
            onClick={() => setOpenModel(true)}
            className="flex items-center justify-center rounded-full text-gray-300 hover:text-white transition-colors"
            style={{
              width: "36px",
              height: "36px",
              background: "#2e2e2e",
              fontSize: "20px",
              border: "none",
              cursor: "pointer",
            }}
          >
            +
          </button>
        </div>

        <div
          style={{
            height: "6px",
            background: "#2e2e2e",
            borderRadius: "999px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              width: `${progress}%`,
              background: "linear-gradient(90deg, #22c55e, #4ade80)",
              borderRadius: "999px",
              transition: "width 0.4s ease",
            }}
          />
        </div>
      </div>
      {openModel && (
        <Modal
          closeModal={setOpenModel}
          setCurrent={setCurrent}
          label={label}
          unit={unit}
        />
      )}
    </div>
  );
}
