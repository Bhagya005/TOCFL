import { NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { refreshUserStats } from "@/lib/db";
import { normalizePinyinForComparison } from "@/lib/pinyin";
import { getCurrentStudyDay } from "@/lib/study-progress";
import { supabase } from "@/lib/supabase-server";

export async function POST(request: Request) {
  let user: { id: number; username: string };
  try {
    user = await requireAuth(request);
  } catch (res) {
    if (res instanceof Response) return res;
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const body = await request.json().catch(() => ({}));
  const testType = String(body?.test_type ?? "").toLowerCase();
  const answers = body?.answers ?? {};
  const today = new Date().toISOString().slice(0, 10);

  const { data: cached } = await supabase
    .from("generated_tests")
    .select("payload_json")
    .eq("user_id", user.id)
    .eq("date", today)
    .eq("test_type", testType)
    .single();

  if (!cached?.payload_json) {
    return NextResponse.json(
      { detail: "No test in progress" },
      { status: 400 }
    );
  }

  const payload = cached.payload_json as { questions?: Record<string, unknown>[] };
  const questions = payload?.questions ?? [];
  const answersMap: Record<number, number | string> = {};
  for (const [k, v] of Object.entries(answers)) {
    const i = parseInt(k, 10);
    if (!Number.isNaN(i)) answersMap[i] = v as number | string;
  }

  let meaningCorrect = 0,
    meaningTotal = 0,
    listeningCorrect = 0,
    listeningTotal = 0,
    writingCorrect = 0,
    writingTotal = 0;
  const reviewRows: Record<string, string>[] = [];

  questions.forEach((q, i) => {
    const section = (q.section as string) ?? "meaning";
    const userAns = answersMap[i];

    if (section === "meaning") {
      meaningTotal++;
      const options = (q.options as string[]) ?? [];
      const correctIdx = Number(q.answer_index ?? -1);
      const correctText = options[correctIdx] ?? "";
      const userText =
        typeof userAns === "number" && options[userAns] !== undefined
          ? options[userAns]
          : "(no answer)";
      const isCorrect = typeof userAns === "number" && userAns === correctIdx;
      if (isCorrect) meaningCorrect++;
      reviewRows.push({
        "Q#": String(i + 1),
        Section: "Meaning",
        Question: String(q.prompt ?? ""),
        "Your answer": userText,
        "Correct answer": correctText,
        Result: isCorrect ? "Correct" : "Incorrect",
      });
    } else if (section === "listening") {
      listeningTotal++;
      const options = (q.options as string[]) ?? [];
      const correctIdx = Number(q.answer_index ?? -1);
      const correctText = options[correctIdx] ?? "";
      const userText =
        typeof userAns === "number" && options[userAns] !== undefined
          ? options[userAns]
          : "(no answer)";
      const isCorrect = typeof userAns === "number" && userAns === correctIdx;
      if (isCorrect) listeningCorrect++;
      const displayCn = String(q.display_cn ?? "").trim();
      const displayPy = String(q.display_py ?? "").trim();
      const questionText =
        displayCn && displayPy ? `${displayCn} (${displayPy})` : displayCn || "(listening)";
      reviewRows.push({
        "Q#": String(i + 1),
        Section: "Listening",
        Question: questionText,
        "Your answer": userText,
        "Correct answer": correctText,
        Result: isCorrect ? "Correct" : "Incorrect",
      });
    } else {
      writingTotal++;
      const correctPinyinNumbers = String(q.correct_pinyin_numbers ?? "").trim();
      const correctPinyinDisplay = String(q.correct_pinyin_display ?? "").trim();
      const userText =
        typeof userAns === "string" && String(userAns).trim()
          ? String(userAns).trim()
          : "(no answer)";
      // Normalize: convert tone numbers → tone marks, then strip to base vowels; compare.
      const normalizedUser = normalizePinyinForComparison(userText);
      const normalizedCorrect = normalizePinyinForComparison(correctPinyinNumbers);
      const isCorrect = Boolean(
        normalizedUser &&
        normalizedCorrect &&
        normalizedUser === normalizedCorrect
      );
      if (isCorrect) writingCorrect++;
      reviewRows.push({
        "Q#": String(i + 1),
        Section: "Writing",
        Question: `English: ${String(q.prompt ?? "")}`,
        "Your answer": userText,
        "Correct answer": correctPinyinDisplay || correctPinyinNumbers,
        Result: isCorrect ? "Correct" : "Incorrect",
      });
    }
  });

  const total = questions.length;
  const totalCorrect = meaningCorrect + listeningCorrect + writingCorrect;
  const accuracyPercent = total > 0 ? (100.0 * totalCorrect) / total : 0;

  const payloadWithStudyDay = payload as { study_day?: number };
  const studyDay =
    testType === "daily"
      ? payloadWithStudyDay?.study_day ?? (await getCurrentStudyDay(user.id))
      : null;

  const insertRow: Record<string, unknown> = {
    user_id: user.id,
    date: today,
    test_type: testType,
    score: totalCorrect,
    total,
    meta_json: {
      version: 2,
      meaning_score: meaningCorrect,
      listening_score: listeningCorrect,
      writing_score: writingCorrect,
      accuracy_percent: Math.round(accuracyPercent * 10) / 10,
    },
  };
  if (testType === "daily" && studyDay != null) insertRow.study_day = studyDay;

  // Daily test: store only the best score for (user, date, study_day). User can retake unlimited times.
  if (testType === "daily" && studyDay != null) {
    const { data: existing } = await supabase
      .from("test_results")
      .select("id, score")
      .eq("user_id", user.id)
      .eq("date", today)
      .eq("test_type", "daily")
      .eq("study_day", studyDay);
    const bestExisting = (existing ?? []).reduce((max, r) => Math.max(max, Number(r.score)), -1);
    if (totalCorrect <= bestExisting) {
      // This attempt is not better; don't insert. Return success with current best.
      await refreshUserStats(user.id);
      return NextResponse.json({
        total_correct: totalCorrect,
        total,
        accuracy_percent: accuracyPercent,
        meaning_score: meaningCorrect,
        meaning_total: meaningTotal,
        listening_score: listeningCorrect,
        listening_total: listeningTotal,
        writing_score: writingCorrect,
        writing_total: writingTotal,
        review_rows: reviewRows,
        already_completed: false,
        best_score_saved: bestExisting,
      });
    }
    // New best: remove previous rows for this (user, date, study_day) and insert this one.
    await supabase
      .from("test_results")
      .delete()
      .eq("user_id", user.id)
      .eq("date", today)
      .eq("test_type", "daily")
      .eq("study_day", studyDay);
  }

  await supabase.from("test_results").insert(insertRow);

  await refreshUserStats(user.id);

  return NextResponse.json({
    total_correct: totalCorrect,
    total,
    accuracy_percent: accuracyPercent,
    meaning_score: meaningCorrect,
    meaning_total: meaningTotal,
    listening_score: listeningCorrect,
    listening_total: listeningTotal,
    writing_score: writingCorrect,
    writing_total: writingTotal,
    review_rows: reviewRows,
    already_completed: false,
  });
}
