"use client";

import { useState } from "react";
import { triggerETLSync } from "@/lib/api";

export default function SyncButton() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ type: "success" | "error"; msg: string } | null>(null);

  const handleSync = async () => {
    setLoading(true);
    setResult(null);
    try {
      const data = await triggerETLSync();
      setResult({ type: "success", msg: `${data.registros_procesados} registros procesados` });
    } catch (e: unknown) {
      setResult({ type: "error", msg: e instanceof Error ? e.message : "Error desconocido" });
    } finally {
      setLoading(false);
      setTimeout(() => setResult(null), 4000);
    }
  };

  return (
    <>
      <button
        id="btn-sync-etl"
        className="btn-primary"
        onClick={handleSync}
        disabled={loading}
      >
        {loading ? (
          <>
            <span className="spinner" />
            Sincronizando...
          </>
        ) : (
          <>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 2v6h-6" /><path d="M3 12a9 9 0 0 1 15-6.7L21 8" />
              <path d="M3 22v-6h6" /><path d="M21 12a9 9 0 0 1-15 6.7L3 16" />
            </svg>
            Forzar Sincronización
          </>
        )}
      </button>
      {result && (
        <div className="toast-container">
          <div className={`toast toast-${result.type}`}>{result.msg}</div>
        </div>
      )}
    </>
  );
}
