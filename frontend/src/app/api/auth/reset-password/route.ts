import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabase-server";
import { hashPassword } from "@/lib/password";

const NO_CACHE_HEADERS = {
  "Cache-Control": "no-store, no-cache, private, max-age=0",
  Pragma: "no-cache",
};

const INVISIBLE_REGEX = /[\u200B-\u200D\u2060\uFEFF\u00AD]/g;

function normalizeInput(s: string): string {
  return s
    .trim()
    .replace(INVISIBLE_REGEX, "")
    .normalize("NFC");
}

export async function POST(request: Request) {
  try {
    const body = await request.json().catch(() => ({}));
    const username = normalizeInput(String(body?.username ?? ""));
    const newPassword = normalizeInput(String(body?.new_password ?? ""));

    if (!username || !newPassword) {
      return NextResponse.json(
        { detail: "Username and new password are required" },
        { status: 400, headers: NO_CACHE_HEADERS }
      );
    }

    if (newPassword.length < 4) {
      return NextResponse.json(
        { detail: "Password must be at least 4 characters" },
        { status: 400, headers: NO_CACHE_HEADERS }
      );
    }

    const norm = (s: string) => (s ?? "").trim().normalize("NFC").replace(INVISIBLE_REGEX, "");

    let row: { id: number; username: string } | null = null;
    const { data: exactRow, error: exactError } = await supabase
      .from("users")
      .select("id, username")
      .eq("username", username)
      .maybeSingle();

    if (!exactError && exactRow) {
      row = exactRow as { id: number; username: string };
    }

    if (!row) {
      const { data: users, error } = await supabase.from("users").select("id, username");
      if (!error && users?.length) {
        const found =
          users.find((u) => norm(u.username) === username) ??
          users.find((u) => norm(u.username).toLowerCase() === username.toLowerCase());
        if (found) row = found as { id: number; username: string };
      }
    }

    if (row) {
      const passwordHash = hashPassword(newPassword);
      await supabase.from("users").update({ password_hash: passwordHash }).eq("id", row.id);
    }

    return NextResponse.json(
      {
        message:
          "If that username exists, the password has been reset. You can log in with your new password.",
      },
      { headers: NO_CACHE_HEADERS }
    );
  } catch {
    return NextResponse.json(
      { detail: "Something went wrong. Please try again." },
      { status: 400, headers: NO_CACHE_HEADERS }
    );
  }
}
