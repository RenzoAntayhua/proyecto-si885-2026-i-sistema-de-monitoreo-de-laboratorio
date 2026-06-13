"use client";

import { Computadora } from "@/lib/api";

interface PcTableProps {
  pcs: Computadora[];
}

export default function PcTable({ pcs }: PcTableProps) {
  if (pcs.length === 0) {
    return (
      <div style={{ textAlign: "center", padding: 48, color: "var(--text-muted)" }}>
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: "0 auto 16px", display: "block", opacity: 0.4 }}>
          <rect x="2" y="3" width="20" height="14" rx="2" /><path d="M8 21h8" /><path d="M12 17v4" />
        </svg>
        No hay computadoras registradas. Usa el instalador para registrar PCs.
      </div>
    );
  }

  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Hostname</th>
          <th>IP Local</th>
          <th>Laboratorio</th>
          <th>Registrado</th>
        </tr>
      </thead>
      <tbody>
        {pcs.map((pc) => (
          <tr key={pc.id}>
            <td style={{ fontWeight: 600 }}>{pc.hostname}</td>
            <td>
              <code style={{ background: "var(--bg-tertiary)", padding: "3px 8px", borderRadius: 6, fontSize: 13 }}>
                {pc.ip_local || "N/A"}
              </code>
            </td>
            <td>
              <span className="badge badge-cyan">{pc.laboratorio_nombre || "—"}</span>
            </td>
            <td style={{ color: "var(--text-muted)", fontSize: 13 }}>
              {new Date(pc.registrado_en).toLocaleDateString("es-PE", {
                day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit"
              })}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
