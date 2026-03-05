import { useState } from "react";
import "./App.css";

function App() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-black gap-4">
      <Card emoji="🚶" label="Walk" goal={10000} unit="steps" />
      <Card emoji="💧" label="Water" goal={8} unit="glasses" />
      <Card emoji="📚" label="Read" goal={30} unit="minutes" />
    </div>
  );
}

function Card({ emoji, label, goal, unit }) {
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

function AddCard() {}

function Modal({ closeModal, setCurrent, label, unit }) {
  const [value, setValue] = useState("");

  function handleAdd() {
    const amount = Number(value);
    if (!amount || amount <= 0) return;

    setCurrent((prev) => prev + amount);
    setValue("");
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
        <p className="text-white font-bold text-xl">Add {label}</p>
        <input
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              handleAdd();
            }
          }}
          type="number"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={`Enter ${unit}`}
          className="w-full px-4 py-3 rounded-xl text-white outline-none text-base"
          style={{ background: "#2a3147", border: "1px solid #3a4160" }}
        ></input>
        <div className="flex flex-col gap-2">
          <button
            onClick={() => closeModal(false)}
            className="w-full py-3 rounded-xl text-white font-semibold text-base transition-opacity hover:opacity-80"
            style={{ background: "#2e3650" }}
          >
            Cancel
          </button>
        </div>
        <div>
          <button
            onClick={handleAdd}
            className="w-full py-3 rounded-xl font-bold text-base transition-opacity hover:opacity-80"
            style={{ background: "#22c55e", color: "#000" }}
          >
            Add
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
