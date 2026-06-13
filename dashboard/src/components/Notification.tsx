"use client";

import { useEffect, useState } from "react";

interface Toast {
  id: number;
  type: "success" | "error";
  message: string;
}

let toastId = 0;
const listeners: Set<(toast: Toast) => void> = new Set();

export function showToast(type: "success" | "error", message: string) {
  const toast: Toast = { id: ++toastId, type, message };
  listeners.forEach((fn) => fn(toast));
}

export default function Notification() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const handler = (toast: Toast) => {
      setToasts((prev) => [...prev, toast]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== toast.id));
      }, 4000);
    };
    listeners.add(handler);
    return () => { listeners.delete(handler); };
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.type}`}>
          {t.type === "success" ? "✓ " : "✕ "}{t.message}
        </div>
      ))}
    </div>
  );
}
