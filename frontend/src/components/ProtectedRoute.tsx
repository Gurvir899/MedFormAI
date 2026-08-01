"use client";

import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

export function ProtectedRoute({ children, roles }: { children: ReactNode; roles?: string[] }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
    if (!loading && user && roles && !roles.includes(user.role)) {
      router.push("/dashboard");
    }
  }, [user, loading, router, roles]);

  if (loading) {
    return (
      <div style={{ padding: "4rem", textAlign: "center" }}>
        <span className="spinner" style={{ borderTopColor: "var(--primary)" }} /> Loading...
      </div>
    );
  }
  if (!user) return null;
  if (roles && !roles.includes(user.role)) return null;

  return <>{children}</>;
}
