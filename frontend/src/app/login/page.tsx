"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ maxWidth: "440px", margin: "4rem auto", padding: "0 1rem" }}>
      <div style={{ textAlign: "center", marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "2rem", marginBottom: "0.25rem" }}>
          <Link href="/" style={{ color: "inherit", textDecoration: "none" }}>Paean</Link>
        </h1>
        <p style={{ fontFamily: "var(--fontSerif)", fontSize: "1.125rem", color: "var(--textMuted)", fontStyle: "italic" }}>
          Sign in to your account
        </p>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "1rem" }}>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="dr.smith@clinic.ca"
              required
              autoFocus
            />
          </div>

          <div style={{ marginBottom: "1.5rem" }}>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          {error && (
            <div className="badge badgeDanger" style={{ display: "block", padding: "0.625rem", marginBottom: "1rem", textAlign: "center" }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            className="primary"
            disabled={loading || !email || !password}
            style={{ width: "100%", padding: "0.75rem", fontSize: "1rem" }}
          >
            {loading ? <><span className="spinner" /> Signing in...</> : "Sign In"}
          </button>
        </form>

        <p style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "0.875rem", color: "var(--textMuted)" }}>
          Don&apos;t have an account?{" "}
          <Link href="/signup" style={{ color: "var(--primaryLight)", fontWeight: 500 }}>
            Sign up
          </Link>
        </p>
      </div>
    </main>
  );
}
