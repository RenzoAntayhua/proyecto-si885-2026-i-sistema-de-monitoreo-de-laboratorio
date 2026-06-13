"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  {
    href: "/",
    label: "Dashboard",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
      </svg>
    ),
  },
  {
    href: "/laboratorios",
    label: "Laboratorios",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 3h6v8l4 7H5l4-7V3z" /><path d="M9 3h6" />
      </svg>
    ),
  },
  {
    href: "/computadoras",
    label: "Computadoras",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2" /><path d="M8 21h8" /><path d="M12 17v4" />
      </svg>
    ),
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      style={{
        width: "var(--sidebar-width)",
        minHeight: "100vh",
        background: "var(--bg-secondary)",
        borderRight: "1px solid var(--border-glass)",
        padding: "24px 16px",
        position: "fixed",
        top: 0,
        left: 0,
        zIndex: 50,
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Logo */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 40, padding: "0 8px" }}>
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: 10,
            background: "var(--gradient-primary)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="2" /><path d="M12 2v4" /><path d="M12 18v4" />
            <path d="m4.93 4.93 2.83 2.83" /><path d="m16.24 16.24 2.83 2.83" />
            <path d="M2 12h4" /><path d="M18 12h4" />
            <path d="m4.93 19.07 2.83-2.83" /><path d="m16.24 7.76 2.83-2.83" />
          </svg>
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: 15, color: "var(--text-primary)" }}>NetMonitor</div>
          <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Panel de Control</div>
        </div>
      </div>

      {/* Nav Links */}
      <nav style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        {links.map((link) => {
          const isActive = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "10px 14px",
                borderRadius: 10,
                textDecoration: "none",
                fontSize: 14,
                fontWeight: isActive ? 600 : 400,
                color: isActive ? "var(--accent-cyan)" : "var(--text-secondary)",
                background: isActive ? "rgba(6, 182, 212, 0.1)" : "transparent",
                transition: "all 0.2s ease",
              }}
            >
              {link.icon}
              {link.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div style={{ marginTop: "auto", padding: "0 8px" }}>
        <div
          style={{
            padding: 16,
            borderRadius: 12,
            background: "var(--bg-tertiary)",
            border: "1px solid var(--border-glass)",
          }}
        >
          <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 4 }}>
            Sistema v1.0
          </div>
          <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
            Monitoreo de Red Distribuido
          </div>
        </div>
      </div>
    </aside>
  );
}
