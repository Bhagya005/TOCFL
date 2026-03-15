"use client";

import { Suspense, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login, register } from "@/lib/api";
import LoginSessionMessage from "./LoginSessionMessage";

export default function LoginPage() {
  const router = useRouter();
  const [tab, setTab] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const n = (s: string) => s.trim().normalize("NFC");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await login(n(username), n(password));
      router.push("/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");
    if (!username.trim() || !password) {
      setError("Username and password required");
      return;
    }
    try {
      await register(n(username), n(password));
      setMessage("Account created. You can log in now.");
      setTab("login");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-lg bg-gray-800 p-6 shadow-xl">
        <h1 className="text-2xl font-bold text-center mb-6">TOCFL A1 Study</h1>
        <Suspense fallback={null}>
          <LoginSessionMessage />
        </Suspense>
        {message && <p className="text-amber-400 text-sm text-center mb-4">{message}</p>}
        <p className="text-gray-400 text-base font-medium text-center mb-6">Create up to 5 users. Each has separate progress.</p>
        <div className="flex gap-2 mb-6">
          <button
            type="button"
            onClick={() => setTab("login")}
            className={`flex-1 py-2 rounded ${tab === "login" ? "bg-amber-600 text-white" : "bg-gray-700 text-gray-300"}`}
          >
            Log in
          </button>
          <button
            type="button"
            onClick={() => setTab("register")}
            className={`flex-1 py-2 rounded ${tab === "register" ? "bg-amber-600 text-white" : "bg-gray-700 text-gray-300"}`}
          >
            Create user
          </button>
        </div>
        {error && <p className="text-red-400 text-base font-medium mb-4">{error}</p>}
        {message && <p className="text-green-400 text-base font-medium mb-4">{message}</p>}
        {tab === "login" ? (
          <>
            <form onSubmit={handleLogin} className="space-y-4">
              <input
                type="text"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2 rounded bg-gray-700 border border-gray-600 text-white placeholder-gray-400"
              />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 rounded bg-gray-700 border border-gray-600 text-white placeholder-gray-400"
              />
              <button type="submit" className="w-full py-2 rounded bg-amber-600 hover:bg-amber-500 text-white font-medium">
                Log in
              </button>
            </form>
            <p className="mt-4 text-center">
              <Link
                href="/forgot-password"
                className="text-amber-400 hover:text-amber-300 text-sm font-medium"
              >
                Forgot password?
              </Link>
            </p>
          </>
        ) : (
          <form onSubmit={handleRegister} className="space-y-4">
            <input
              type="text"
              placeholder="New username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 rounded bg-gray-700 border border-gray-600 text-white placeholder-gray-400"
            />
            <input
              type="password"
              placeholder="New password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 rounded bg-gray-700 border border-gray-600 text-white placeholder-gray-400"
            />
            <button type="submit" className="w-full py-2 rounded bg-amber-600 hover:bg-amber-500 text-white font-medium">
              Create user
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
