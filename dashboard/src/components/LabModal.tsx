"use client";

import { useState, useEffect } from "react";
import { Laboratorio, LaboratorioCreate, fetchLaboratorios, crearLaboratorio, actualizarLaboratorio, eliminarLaboratorio } from "@/lib/api";

interface LabModalProps {
  open: boolean;
  lab: Laboratorio | null;
  onClose: () => void;
  onSaved: () => void;
}

export default function LabModal({ open, lab, onClose, onSaved }: LabModalProps) {
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (lab) {
      setNombre(lab.nombre);
      setDescripcion(lab.descripcion || "");
    } else {
      setNombre("");
      setDescripcion("");
    }
    setError("");
  }, [lab, open]);

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nombre.trim()) { setError("El nombre es obligatorio."); return; }
    setLoading(true);
    setError("");
    try {
      const data: LaboratorioCreate = { nombre: nombre.trim(), descripcion: descripcion.trim() || undefined };
      if (lab) {
        await actualizarLaboratorio(lab.id, data);
      } else {
        await crearLaboratorio(data);
      }
      onSaved();
      onClose();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al guardar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2>{lab ? "Editar Laboratorio" : "Nuevo Laboratorio"}</h2>
        <form onSubmit={handleSubmit}>
          <label htmlFor="lab-nombre">Nombre</label>
          <input
            id="lab-nombre"
            type="text"
            placeholder="Ej: LAB-101"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            autoFocus
          />
          <label htmlFor="lab-descripcion">Descripción</label>
          <textarea
            id="lab-descripcion"
            placeholder="Descripción del laboratorio (opcional)"
            rows={3}
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
          />
          {error && (
            <div style={{ color: "var(--accent-rose)", fontSize: 13, marginBottom: 12 }}>{error}</div>
          )}
          <div className="modal-actions">
            <button type="button" className="btn-ghost" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? <span className="spinner" /> : null}
              {lab ? "Guardar Cambios" : "Crear Laboratorio"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
