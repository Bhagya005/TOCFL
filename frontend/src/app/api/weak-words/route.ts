import { NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { supabase } from "@/lib/supabase-server";

export async function GET(request: Request) {
  let user: { id: number; username: string };
  try {
    user = await requireAuth(request);
  } catch (res) {
    if (res instanceof Response) return res;
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const { data: weakRows } = await supabase
    .from("weak_words")
    .select("word_id")
    .eq("user_id", user.id);

  const wordIds = (weakRows ?? []).map((r) => r.word_id);
  if (wordIds.length === 0) {
    return NextResponse.json({ words: [] });
  }

  const { data: words } = await supabase
    .from("words")
    .select("id, character, pinyin, meaning, pos")
    .in("id", wordIds)
    .order("id");

  return NextResponse.json({
    words: (words ?? []).map((w) => ({
      id: w.id,
      character: w.character,
      pinyin: w.pinyin,
      meaning: w.meaning,
      pos: w.pos,
    })),
  });
}
