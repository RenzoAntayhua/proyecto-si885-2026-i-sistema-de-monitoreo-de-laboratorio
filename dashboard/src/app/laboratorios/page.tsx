"use client";

import { useEffect, useState, useCallback } from "react";
import { Laboratorio, fetchLaboratorios } from "@/lib/api";
import LabTable from "@/components/LabTable";
import LabModal from "@/components/LabModal";

export default function LaboratoriosPage() {
  const [labs, setLabs] = useState<Laboratorio[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingLab, setEditingLab] = useState<Laboratorio | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchLaboratorios();
      setLabs(data);
    } catch {
      setLabs([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openCreate = () => { setEditingLab(null); setModalOpen(true); };
  const openEdit = (lab: Laboratorio) => { setEditingLab(lab); setModalOpen(true); };
  const closeModal = () => { setModalOpen(false); setEditingLab(null); };

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 28 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Laboratorios</h2>
          <p style={{ margin: "4px 0 0", fontSize: 14, color: "var(--text-muted)" }}>
            Gestiona los laboratorios de cómputo del sistema
          </p>
        </div>
        <button id="btn-crear-lab" className="btn-primary" onClick={openCreate}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M12 5v14" /><path d="M5 12h14" />
          </svg>
          Nuevo Laboratorio
        </button>
      </div>

      <div className="glass-card" style={{ padding: 0, overflow: "hidden" }}>
        {loading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: 48 }}>
            <div className="spinner" style={{ width: 28, height: 28, borderWidth: 3 }} />
          </div>
        ) : (
          <LabTable labs={labs} onEdit={openEdit} onRefresh={load} />
        )}
      </div>

      <LabModal open={modalOpen} lab={editingLab} onClose={closeModal} onSaved={load} />
    </div>
  );
}
