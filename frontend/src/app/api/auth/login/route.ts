import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabase-server";
import { encodeToken } from "@/lib/auth";
import { verifyPassword } from "@/lib/password";

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

async function getLoginBody(request: Request): Promise<{ username: string; password: string } | null> {
  const contentType = (request.headers.get("content-type") ?? "").toLowerCase();
  if (contentType.includes("application/json")) {
    const body = await request.json().catch(() => null);
    if (body && typeof body === "object") {
      return {
        username: normalizeInput(String(body.username ?? "")),
        password: normalizeInput(String(body.password ?? "")),
      };
    }
  }
  if (contentType.includes("application/x-www-form-urlencoded") || contentType.includes("multipart/form-data")) {
    const form = await request.formData().catch(() => null);
    if (form) {
      return {
        username: normalizeInput(String(form.get("username") ?? "")),
        password: normalizeInput(String(form.get("password") ?? "")),
      };
    }
  }
  return null;
}

export async function POST(request: Request) {
  try {
    const body = await getLoginBody(request);
    if (!body) {
      return NextResponse.json(
        { detail: "Username and password required" },
        { status: 400, headers: NO_CACHE_HEADERS }
      );
    }
    const { username, password } = body;
    if (!username || !password) {
      return NextResponse.json(
        { detail: "Username and password required" },
        { status: 400, headers: NO_CACHE_HEADERS }
      );
    }

    const { data: users, error } = await supabase
      .from("users")
      .select("id, username, password_hash");

    if (error) {
      return NextResponse.json(
        { detail: "Invalid username or password" },
        { status: 401, headers: NO_CACHE_HEADERS }
      );
    }

    const norm = (s: string) => (s ?? "").trim().normalize("NFC");
    const row =
      users?.find((u) => norm(u.username) === username) ??
      users?.find((u) => norm(u.username).toLowerCase() === username.toLowerCase());
    if (!row || !row.password_hash) {
      return NextResponse.json(
        { detail: "Invalid username or password" },
        { status: 401, headers: NO_CACHE_HEADERS }
      );
    }

    const storedHash = String(row.password_hash).trim();
    const passwordNfc = password.normalize("NFC");
    const verified =
      verifyPassword(password, storedHash) ||
      (password !== passwordNfc && verifyPassword(passwordNfc, storedHash));
    if (!verified) {
      return NextResponse.json(
        { detail: "Invalid username or password" },
        { status: 401, headers: NO_CACHE_HEADERS }
      );
    }

    const token = await encodeToken(Number(row.id), row.username);
    return NextResponse.json(
      {
        token,
        user: { id: Number(row.id), username: row.username },
      },
      { headers: NO_CACHE_HEADERS }
    );
  } catch {
    return NextResponse.json(
      { detail: "Invalid request" },
      { status: 400, headers: NO_CACHE_HEADERS }
    );
  }
}
