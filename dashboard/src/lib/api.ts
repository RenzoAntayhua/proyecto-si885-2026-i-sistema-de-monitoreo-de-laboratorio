const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Laboratorio {
  id: string;
  nombre: string;
  descripcion: string | null;
  creado_en: string;
  total_computadoras: number;
}

export interface LaboratorioCreate {
  nombre: string;
  descripcion?: string;
}

export interface Computadora {
  id: string;
  hostname: string;
  laboratorio_id: string;
  ip_local: string | null;
  registrado_en: string;
  laboratorio_nombre: string | null;
}

export interface Stats {
  total_laboratorios: number;
  total_computadoras: number;
  total_trafico: number;
}

export interface ETLSyncResult {
  registros_procesados: number;
  mensaje: string;
}

// ── Laboratorios ────────────────────────────────────────────────────────────

export async function fetchLaboratorios(): Promise<Laboratorio[]> {
  const res = await fetch(`${API_BASE}/api/laboratorios/`, { cache: "no-store" });
  if (!res.ok) throw new Error("Error al obtener laboratorios");
  return res.json();
}

export async function crearLaboratorio(data: LaboratorioCreate): Promise<Laboratorio> {
  const res = await fetch(`${API_BASE}/api/laboratorios/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Error al crear laboratorio");
  }
  return res.json();
}

export async function actualizarLaboratorio(id: string, data: LaboratorioCreate): Promise<Laboratorio> {
  const res = await fetch(`${API_BASE}/api/laboratorios/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Error al actualizar laboratorio");
  }
  return res.json();
}

export async function eliminarLaboratorio(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/laboratorios/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Error al eliminar laboratorio");
}

// ── Computadoras ────────────────────────────────────────────────────────────

export async function fetchComputadoras(): Promise<Computadora[]> {
  const res = await fetch(`${API_BASE}/api/computadoras/`, { cache: "no-store" });
  if (!res.ok) throw new Error("Error al obtener computadoras");
  return res.json();
}

// ── Stats ───────────────────────────────────────────────────────────────────

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${API_BASE}/api/stats/`, { cache: "no-store" });
  if (!res.ok) throw new Error("Error al obtener estadísticas");
  return res.json();
}

// ── ETL ─────────────────────────────────────────────────────────────────────

export async function triggerETLSync(): Promise<ETLSyncResult> {
  const res = await fetch(`${API_BASE}/api/etl/sync`, { method: "POST" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Error en la sincronización ETL");
  }
  return res.json();
}
