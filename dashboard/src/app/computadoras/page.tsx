"use client";

import { useEffect, useState } from "react";
import { Computadora, fetchComputadoras } from "@/lib/api";
import PcTable from "@/components/PcTable";

export default function ComputadorasPage() {
  const [pcs, setPcs] = useState<Computadora[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchComputadoras();
        setPcs(data);
      } catch {
        setPcs([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Computadoras</h2>
        <p style={{ margin: "4px 0 0", fontSize: 14, color: "var(--text-muted)" }}>
          PCs registradas en los laboratorios con agente Wazuh instalado
        </p>
      </div>

      <div className="glass-card" style={{ padding: 0, overflow: "hidden" }}>
        {loading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: 48 }}>
            <div className="spinner" style={{ width: 28, height: 28, borderWidth: 3 }} />
          </div>
        ) : (
          <PcTable pcs={pcs} />
        )}
      </div>
    </div>
  );
}
