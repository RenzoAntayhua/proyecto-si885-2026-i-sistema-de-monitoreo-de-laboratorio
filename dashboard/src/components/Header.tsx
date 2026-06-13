import SyncButton from "./SyncButton";

export default function Header() {
  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "16px 32px",
        borderBottom: "1px solid var(--border-glass)",
        background: "rgba(17, 24, 39, 0.6)",
        backdropFilter: "blur(12px)",
        position: "sticky",
        top: 0,
        zIndex: 40,
      }}
    >
      <div>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>
          Monitoreo de Red
        </h1>
        <p style={{ margin: 0, fontSize: 13, color: "var(--text-muted)" }}>
          Laboratorios de Cómputo
        </p>
      </div>
      <SyncButton />
    </header>
  );
}
