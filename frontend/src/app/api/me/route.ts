import { NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";

export async function GET(request: Request) {
  try {
    const user = await requireAuth(request);
    return NextResponse.json({ id: user.id, username: user.username });
  } catch (res) {
    if (res instanceof Response) return res;
    return NextResponse.json(
      { detail: "Not authenticated" },
      { status: 401 }
    );
  }
}
