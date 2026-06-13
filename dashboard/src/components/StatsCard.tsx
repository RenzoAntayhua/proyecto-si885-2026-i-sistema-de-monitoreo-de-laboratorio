interface StatsCardProps {
  title: string;
  value: number | string;
  gradient: string;
  icon: React.ReactNode;
}

export default function StatsCard({ title, value, gradient, icon }: StatsCardProps) {
  return (
    <div
      className="glass-card"
      style={{
        padding: 24,
        background: gradient,
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Decorative circle */}
      <div
        style={{
          position: "absolute",
          top: -20,
          right: -20,
          width: 80,
          height: 80,
          borderRadius: "50%",
          background: "rgba(255,255,255,0.04)",
        }}
      />
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <div
          style={{
            width: 44,
            height: 44,
            borderRadius: 12,
            background: "rgba(255,255,255,0.08)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {icon}
        </div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text-secondary)", marginBottom: 2 }}>
            {title}
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, letterSpacing: "-0.02em" }}>
            {typeof value === "number" ? value.toLocaleString() : value}
          </div>
        </div>
      </div>
    </div>
  );
}
