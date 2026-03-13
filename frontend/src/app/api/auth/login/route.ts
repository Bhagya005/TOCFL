import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabase-server";
import { encodeToken } from "@/lib/auth";
import { verifyPassword } from "@/lib/password";

const NO_CACHE_HEADERS = {
  "Cache-Control": "no-store, no-cache, private, max-age=0",
  Pragma: "no-cache",
};

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const username = String(body?.username ?? "").trim();
    const password = String(body?.password ?? "").trim();
    if (!username || !password) {
      return NextResponse.json(
        { detail: "Username and password required" },
        { status: 400, headers: NO_CACHE_HEADERS }
      );
    }

    const { data: row, error } = await supabase
      .from("users")
      .select("id, username, password_hash")
      .eq("username", username)
      .single();

    if (error || !row) {
      return NextResponse.json(
        { detail: "Invalid username or password" },
        { status: 401, headers: NO_CACHE_HEADERS }
      );
    }

    if (!verifyPassword(password, row.password_hash)) {
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
