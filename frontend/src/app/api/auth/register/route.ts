import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabase-server";
import { encodeToken } from "@/lib/auth";
import { hashPassword } from "@/lib/password";

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

    const { count } = await supabase
      .from("users")
      .select("*", { count: "exact", head: true });
    if ((count ?? 0) >= 5) {
      return NextResponse.json(
        { detail: "User limit reached (5 users)." },
        { status: 400, headers: NO_CACHE_HEADERS }
      );
    }

    const passwordHash = hashPassword(password);
    const { data: user, error } = await supabase
      .from("users")
      .insert({ username, password_hash: passwordHash })
      .select("id, username")
      .single();

    if (error) {
      if (error.code === "23505") {
        return NextResponse.json(
          { detail: "Username may already exist" },
          { status: 400, headers: NO_CACHE_HEADERS }
        );
      }
      throw error;
    }

    await supabase.from("user_settings").insert({ user_id: user.id });
    await supabase.from("user_stats").insert({
      user_id: user.id,
      username: user.username,
    });

    const token = await encodeToken(Number(user.id), user.username);
    return NextResponse.json(
      {
        token,
        user: { id: Number(user.id), username: user.username },
      },
      { headers: NO_CACHE_HEADERS }
    );
  } catch (e) {
    const message =
      e instanceof Error ? e.message : "Registration failed";
    return NextResponse.json(
      { detail: message },
      { status: 400, headers: NO_CACHE_HEADERS }
    );
  }
}
