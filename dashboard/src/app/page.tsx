"use client";

import { useEffect, useState } from "react";
import StatsCard from "@/components/StatsCard";
import { Stats, fetchStats } from "@/lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const data = await fetchStats();
      setStats(data);
    } catch {
      setStats({ total_laboratorios: 0, total_computadoras: 0, total_trafico: 0 });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Carga inicial
    load();

    // Configurar refresco automático cada 30 segundos
    const interval = setInterval(() => {
      load();
    }, 30000);

    // Limpiar intervalo al cerrar la página
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: 300 }}>
        <div className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 32, display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Resumen General</h2>
          <p style={{ margin: "4px 0 0", fontSize: 14, color: "var(--text-muted)" }}>
            Vista consolidada del sistema de monitoreo
          </p>
        </div>
        <a 
          href={`${process.env.NEXT_PUBLIC_API_URL || ""}/api/download-installer`}
          target="_blank"
          rel="noopener noreferrer"
          className="glass-card"
          style={{ 
            padding: "10px 16px", 
            display: "flex", 
            alignItems: "center", 
            gap: 8, 
            textDecoration: "none", 
            color: "var(--accent-cyan)",
            fontSize: 14,
            fontWeight: 600,
            border: "1px solid rgba(0, 255, 255, 0.2)"
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          Descargar Instalador Agente
        </a>
      </div>

      {/* Stats Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 20, marginBottom: 40 }}>
        <StatsCard
          title="Laboratorios"
          value={stats?.total_laboratorios ?? 0}
          gradient="var(--gradient-card-1)"
          icon={
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" strokeWidth="2">
              <path d="M9 3h6v8l4 7H5l4-7V3z" /><path d="M9 3h6" />
            </svg>
          }
        />
        <StatsCard
          title="Computadoras"
          value={stats?.total_computadoras ?? 0}
          gradient="var(--gradient-card-2)"
          icon={
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--accent-emerald)" strokeWidth="2">
              <rect x="2" y="3" width="20" height="14" rx="2" /><path d="M8 21h8" /><path d="M12 17v4" />
            </svg>
          }
        />
        <StatsCard
          title="Registros de Tráfico"
          value={stats?.total_trafico ?? 0}
          gradient="var(--gradient-card-3)"
          icon={
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--accent-violet)" strokeWidth="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          }
        />
      </div>
      
      {/* Power BI Dashboard Section */}
      <div style={{ marginBottom: 40 }}>
        <div style={{ marginBottom: 16 }}>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>Análisis Interactivo de Red (Power BI)</h3>
        </div>
        <div className="glass-card" style={{ padding: 10, overflow: "hidden", borderRadius: 16 }}>
          <iframe 
            title="Dashboard Monitoreo" 
            width="100%" 
            height="600" 
            src="https://app.powerbi.com/reportEmbed?reportId=bffe5f49-9903-44cc-9aaa-0d1e5cfed36f&autoAuth=true&ctid=b6b466ee-468d-4011-b9fc-fbdcf82ac90a" 
            frameBorder="0" 
            allowFullScreen={true}
            style={{ borderRadius: 8, display: "block" }}
          ></iframe>
        </div>
      </div>

      {/* Info Panel */}
      <div className="glass-card" style={{ padding: 28 }}>
        <h3 style={{ margin: "0 0 16px", fontSize: 16, fontWeight: 600 }}>Estado del Sistema</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <div style={{ padding: 16, background: "var(--bg-tertiary)", borderRadius: 10 }}>
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6 }}>Wazuh Manager</div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--accent-emerald)", display: "inline-block" }} />
              <span style={{ fontSize: 14, fontWeight: 500 }}>Configurado</span>
            </div>
          </div>
          <div style={{ padding: 16, background: "var(--bg-tertiary)", borderRadius: 10 }}>
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6 }}>ETL Motor</div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--accent-cyan)", display: "inline-block" }} />
              <span style={{ fontSize: 14, fontWeight: 500 }}>Listo - Usar botón Sincronizar</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
