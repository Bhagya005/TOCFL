"use client";

import { useState } from "react";
import Link from "next/link";

export default function ForgotPasswordPage() {
  const [username, setUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const n = (s: string) => s.trim().normalize("NFC");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");

    if (!username.trim()) {
      setError("Enter your username");
      return;
    }
    if (!newPassword) {
      setError("Enter a new password");
      return;
    }
    if (newPassword.length < 4) {
      setError("Password must be at least 4 characters");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      const base =
        typeof window !== "undefined"
          ? window.location.origin
          : process.env.NEXT_PUBLIC_VERCEL_URL
            ? `https://${process.env.NEXT_PUBLIC_VERCEL_URL}`
            : "http://localhost:3000";
      const res = await fetch(`${base}/api/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          username: n(username),
          new_password: n(newPassword),
        }),
        cache: "no-store",
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(data.detail ?? "Something went wrong");
        return;
      }
      setMessage(data.message ?? "Password has been reset. You can log in now.");
      setUsername("");
      setNewPassword("");
      setConfirmPassword("");
    } catch {
      setError("Could not reach the server. Check your connection.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-lg bg-gray-800 p-6 shadow-xl">
        <h1 className="text-2xl font-bold text-center mb-2">Reset password</h1>
        <p className="text-gray-400 text-sm text-center mb-6">
          Enter your username and choose a new password.
        </p>
        {error && (
          <p className="text-red-400 text-base font-medium mb-4">{error}</p>
        )}
        {message && (
          <p className="text-green-400 text-base font-medium mb-4">{message}</p>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full px-4 py-2 rounded bg-gray-700 border border-gray-600 text-white placeholder-gray-400"
            autoComplete="username"
          />
          <input
            type="password"
            placeholder="New password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="w-full px-4 py-2 rounded bg-gray-700 border border-gray-600 text-white placeholder-gray-400"
            autoComplete="new-password"
            minLength={4}
          />
          <input
            type="password"
            placeholder="Confirm new password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full px-4 py-2 rounded bg-gray-700 border border-gray-600 text-white placeholder-gray-400"
            autoComplete="new-password"
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 rounded bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white font-medium"
          >
            {loading ? "Resetting…" : "Reset password"}
          </button>
        </form>
        <p className="mt-6 text-center">
          <Link
            href="/login"
            className="text-amber-400 hover:text-amber-300 text-sm font-medium"
          >
            ← Back to log in
          </Link>
        </p>
      </div>
    </div>
  );
}
