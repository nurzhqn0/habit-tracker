import { useState } from "react";

export function Modal({ closeModal, setCurrent, label, unit }) {
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
