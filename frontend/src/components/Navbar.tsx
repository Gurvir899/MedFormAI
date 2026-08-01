"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export function Navbar() {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  return (
    <nav style={{
      borderBottom: "1px solid var(--border)",
      background: "var(--surface)",
      padding: "0.75rem 1.5rem",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      position: "sticky",
      top: 0,
      zIndex: 100,
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
        {user ? (
          <>
            <Link href="/dashboard" style={{ fontSize: "0.875rem", fontWeight: 500 }}>
              Dashboard
            </Link>
            <span style={{ fontSize: "0.875rem", color: "var(--textMuted)" }}>
              {user.firstName} {user.lastName}
            </span>
            <span className="badge badgeInfo" style={{ textTransform: "capitalize" }}>
              {user.role}
            </span>
            <button className="secondary" onClick={handleLogout} style={{ fontSize: "0.8125rem", padding: "0.375rem 0.75rem" }}>
              Sign Out
            </button>
          </>
        ) : (
          <>
            <Link href="/login" style={{ fontSize: "0.875rem", fontWeight: 500 }}>
              Physician Sign In
            </Link>
            <Link href="/signup" className="primary" style={{
              display: "inline-block",
              fontSize: "0.875rem",
              padding: "0.375rem 0.875rem",
              borderRadius: "8px",
              color: "white",
            }}>
              Register Clinic
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
