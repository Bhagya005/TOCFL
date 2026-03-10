from __future__ import annotations

import html

import streamlit as st
import streamlit.components.v1 as components


def render_flashcard_card(
    *,
    flipped: bool,
    character: str,
    pinyin: str,
    meaning: str,
    example_cn: str,
    example_py: str,
    example_en: str,
    word_audio_uri: str | None,
    example_audio_uri: str | None,
    image_uri: str | None,
    character_breakdown: list[dict],
    height: int = 420,
) -> None:
    """
    Renders a centered Anki-like card using an HTML component.
    JavaScript works inside this iframe, so we can have real play buttons.
    """
    char_e = html.escape(character)
    pinyin_e = html.escape(pinyin or "")
    meaning_e = html.escape(meaning or "")
    ex_cn_e = html.escape(example_cn or "")
    ex_py_e = html.escape(example_py or "")
    ex_en_e = html.escape(example_en or "")

    def audio_button(audio_id: str, uri: str | None) -> str:
        if not uri:
            return ""
        return f"""
        <button class="play" aria-label="play" onclick="(function(){{var a=document.getElementById('{audio_id}'); a.currentTime=0; a.play();}})()">▶</button>
        <audio id="{audio_id}" src="{uri}"></audio>
        """

    img_html = (
        f"""<img class="pic" src="{image_uri}" alt="image" />""" if image_uri else ""
    )

    breakdown_html = ""
    if character_breakdown:
        rows = []
        for r in character_breakdown:
            c = html.escape(str(r.get("character", "")))
            py = html.escape(str(r.get("pinyin", "")) or "")
            me = html.escape(str(r.get("meaning", "")) or "")
            if not c:
                continue
            rows.append(
                f"""<div class="bd-row"><div class="bd-c">{c}</div><div class="bd-m">{py} {("· " + me) if me else ""}</div></div>"""
            )
        if rows:
            breakdown_html = (
                """<div class="bd"><div class="bd-title">Characters</div>"""
                + "".join(rows)
                + "</div>"
            )

    # Use fixed width matching the visual card width from earlier.
    html_doc = f"""
    <html>
      <head>
        <meta charset="utf-8" />
        <style>
          :root {{
            --bg: rgba(255,255,255,0.04);
            --bd: rgba(255,255,255,0.10);
            --muted: rgba(255,255,255,0.78);
          }}
          body {{
            margin: 0;
            padding: 0;
            background: transparent;
            color: white;
            font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial;
          }}
          .wrap {{
            display: flex;
            justify-content: center;
            padding: 6px 0 10px 0;
          }}
          .card {{
            width: min(760px, 92vw);
            height: {height}px;
            perspective: 1200px;
          }}
          .inner {{
            position: relative;
            width: 100%;
            height: 100%;
            transition: transform 260ms ease;
            transform-style: preserve-3d;
          }}
          .card.flipped .inner {{ transform: rotateY(180deg); }}
          .face {{
            position: absolute;
            inset: 0;
            border-radius: 16px;
            background: var(--bg);
            border: 1px solid var(--bd);
            box-shadow: 0 10px 28px rgba(0,0,0,0.35);
            padding: 22px 26px;
            backface-visibility: hidden;
            overflow: auto;
          }}
          .front {{
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 108px;
            letter-spacing: 2px;
          }}
          .back {{ transform: rotateY(180deg); }}

          .row-center {{
            display:flex;
            align-items:center;
            justify-content:center;
            gap: 14px;
          }}
          .play {{
            width: 44px;
            height: 44px;
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.20);
            background: rgba(255,255,255,0.06);
            color: white;
            font-size: 18px;
            cursor: pointer;
          }}
          .char {{
            font-size: 78px;
            text-align:center;
          }}
          .meta {{
            margin-top: 8px;
            text-align:center;
            font-size: 24px;
            color: var(--muted);
          }}
          .section-title {{
            margin-top: 18px;
            text-align:center;
            font-weight: 800;
            font-size: 20px;
          }}
          .example {{
            margin-top: 10px;
            text-align:center;
          }}
          .ex-cn {{ font-size: 30px; }}
          .ex-py {{ margin-top: 6px; font-size: 20px; color: var(--muted); }}
          .ex-en {{ margin-top: 6px; font-size: 18px; color: var(--muted); }}
          .pic {{
            display:block;
            margin: 16px auto 4px auto;
            width: 150px;
            height: 150px;
            object-fit: contain;
            border-radius: 14px;
            background: rgba(0,0,0,0.20);
            border: 1px solid rgba(255,255,255,0.10);
          }}
          .bd {{
            margin-top: 16px;
            border-top: 1px solid rgba(255,255,255,0.12);
            padding-top: 12px;
          }}
          .bd-title {{
            text-align:center;
            font-weight: 800;
            margin-bottom: 8px;
          }}
          .bd-row {{
            display:flex;
            align-items:baseline;
            justify-content:center;
            gap: 10px;
            margin: 6px 0;
          }}
          .bd-c {{ font-size: 26px; }}
          .bd-m {{ font-size: 18px; color: var(--muted); }}
        </style>
      </head>
      <body>
        <div class="wrap">
          <div class="card {'flipped' if flipped else ''}">
            <div class="inner">
              <div class="face front">{char_e}</div>
              <div class="face back">
                <div class="row-center">
                  {audio_button('w_audio', word_audio_uri)}
                  <div class="char">{char_e}</div>
                </div>
                <div class="meta">{pinyin_e} · {meaning_e}</div>
                {img_html}
                <div class="section-title">Example</div>
                <div class="example">
                  <div class="row-center" style="gap: 12px;">
                    {audio_button('ex_audio', example_audio_uri)}
                    <div class="ex-cn">{ex_cn_e}</div>
                  </div>
                  <div class="ex-py">{ex_py_e}</div>
                  <div class="ex-en">{ex_en_e}</div>
                </div>
                {breakdown_html}
              </div>
            </div>
          </div>
        </div>
      </body>
    </html>
    """

    components.html(html_doc, height=height + 30, scrolling=False)

