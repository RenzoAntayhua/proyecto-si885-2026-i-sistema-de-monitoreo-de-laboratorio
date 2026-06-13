"use client";

import { useState } from "react";
import { Laboratorio, eliminarLaboratorio } from "@/lib/api";

interface LabTableProps {
  labs: Laboratorio[];
  onEdit: (lab: Laboratorio) => void;
  onRefresh: () => void;
}

export default function LabTable({ labs, onEdit, onRefresh }: LabTableProps) {
  const [deleting, setDeleting] = useState<string | null>(null);

  const handleDelete = async (id: string, nombre: string) => {
    if (!confirm(`¿Eliminar el laboratorio "${nombre}" y todas sus computadoras asociadas?`)) return;
    setDeleting(id);
    try {
      await eliminarLaboratorio(id);
      onRefresh();
    } catch {
      alert("Error al eliminar laboratorio");
    } finally {
      setDeleting(null);
    }
  };

  if (labs.length === 0) {
    return (
      <div style={{ textAlign: "center", padding: 48, color: "var(--text-muted)" }}>
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: "0 auto 16px", display: "block", opacity: 0.4 }}>
          <path d="M9 3h6v8l4 7H5l4-7V3z" /><path d="M9 3h6" />
        </svg>
        No hay laboratorios registrados. Crea uno para comenzar.
      </div>
    );
  }

  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Nombre</th>
          <th>Descripción</th>
          <th>PCs</th>
          <th>Creado</th>
          <th style={{ width: 160 }}>Acciones</th>
        </tr>
      </thead>
      <tbody>
        {labs.map((lab) => (
          <tr key={lab.id}>
            <td style={{ fontWeight: 600 }}>
              <span className="badge badge-cyan">{lab.nombre}</span>
            </td>
            <td style={{ color: "var(--text-secondary)", maxWidth: 260, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {lab.descripcion || "—"}
            </td>
            <td>
              <span className="badge badge-violet">{lab.total_computadoras}</span>
            </td>
            <td style={{ color: "var(--text-muted)", fontSize: 13 }}>
              {new Date(lab.creado_en).toLocaleDateString("es-PE", { day: "2-digit", month: "short", year: "numeric" })}
            </td>
            <td>
              <div style={{ display: "flex", gap: 8 }}>
                <button className="btn-ghost" onClick={() => onEdit(lab)}>Editar</button>
                <button
                  className="btn-danger"
                  onClick={() => handleDelete(lab.id, lab.nombre)}
                  disabled={deleting === lab.id}
                >
                  {deleting === lab.id ? "..." : "Eliminar"}
                </button>
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
