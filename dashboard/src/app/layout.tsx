import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import Notification from "@/components/Notification";

export const metadata: Metadata = {
  title: "NetMonitor - Sistema de Monitoreo de Red",
  description: "Panel de administración para el sistema de monitoreo de red distribuido en laboratorios de cómputo.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>
        <Sidebar />
        <div style={{ marginLeft: "var(--sidebar-width)" }}>
          <Header />
          <main style={{ padding: 32 }}>
            {children}
          </main>
        </div>
        <Notification />
      </body>
    </html>
  );
}
