"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { ProtectedRoute } from "@/components/ProtectedRoute";

const navItems = [
  { href: "/dashboard", label: "Overview", icon: "📊" },
  { href: "/dashboard/copilot", label: "Copilot", icon: "🩺", roles: ["doctor", "admin"] },
  { href: "/dashboard/appointments", label: "Appointments", icon: "📅", roles: ["doctor", "admin"] },
  { href: "/dashboard/patients", label: "Patients", icon: "👥", roles: ["doctor", "admin"] },
  { href: "/dashboard/history", label: "History", icon: "📋", roles: ["doctor", "admin"] },
  { href: "/dashboard/compliance", label: "Compliance", icon: "🛡️", roles: ["doctor", "admin"] },
  { href: "/dashboard/roi", label: "ROI Calculator", icon: "💰" },
  { href: "/dashboard/settings", label: "Settings", icon: "⚙️" },
];

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  return (
    <ProtectedRoute>
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        {/* Top bar */}
        <header style={{
          borderBottom: "1px solid var(--border)",
          background: "var(--surface)",
          padding: "0.75rem 1.5rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}>
          <Link href="/" style={{ textDecoration: "none" }}>
            <span style={{
              fontFamily: "var(--fontSerif)",
              fontSize: "1.5rem",
              fontWeight: 700,
              color: "var(--primary)",
            }}>
              Paean
            </span>
          </Link>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <span style={{ fontSize: "0.875rem", color: "var(--textMuted)" }}>
              {user?.firstName} {user?.lastName}
            </span>
            <span className="badge badgeInfo" style={{ textTransform: "capitalize" }}>
              {user?.role}
            </span>
            <button className="secondary" onClick={handleLogout} style={{ fontSize: "0.8125rem", padding: "0.375rem 0.75rem" }}>
              Sign Out
            </button>
          </div>
        </header>

        <div style={{ display: "flex", flex: 1 }}>
          {/* Sidebar */}
          <aside style={{
            width: "220px",
            borderRight: "1px solid var(--border)",
            background: "var(--surface)",
            padding: "1rem 0",
            flexShrink: 0,
          }}>
            {navItems.map((item) => {
              const isAllowed = !item.roles || (user && item.roles.includes(user.role));
              if (!isAllowed) return null;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.625rem",
                    padding: "0.625rem 1.25rem",
                    fontSize: "0.875rem",
                    fontWeight: isActive ? 600 : 400,
                    color: isActive ? "var(--primary)" : "var(--text)",
                    background: isActive ? "#e6f0fa" : "transparent",
                    borderLeft: isActive ? "3px solid var(--primary)" : "3px solid transparent",
                    textDecoration: "none",
                    transition: "background 0.15s",
                  }}
                >
                  <span style={{ fontSize: "1rem" }}>{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </aside>

          {/* Main content */}
          <main style={{ flex: 1, padding: "2rem", maxWidth: "1000px", margin: "0 auto" }}>
            {children}
          </main>
        </div>
      </div>
    </ProtectedRoute>
  );
}
