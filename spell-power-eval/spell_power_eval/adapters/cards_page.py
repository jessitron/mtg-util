"""A self-contained HTML page for judging cards by eye. Shows no model answers and no popularity, so nothing anchors you."""
import html
import json

from ..domain.card import Card
from ..domain.power import Power

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Rate these spells</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; background: #f4f1ea; color: #222; }}
  header {{ position: sticky; top: 0; background: #2b2b3a; color: #fff; padding: .6rem 1rem; z-index: 1; }}
  header p {{ margin: 0 0 .4rem; }}
  textarea {{ width: 100%; height: 6.5rem; font-family: ui-monospace, monospace; }}
  main {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(21rem, 1fr)); gap: 1rem; padding: 1rem; }}
  .card {{ background: #fff; border-radius: .6rem; padding: .8rem; box-shadow: 0 1px 4px #0003; }}
  .card img {{ width: 100%; border-radius: 4%; }}
  .facts {{ font-size: .9rem; margin: .5rem 0; }}
  .facts .text {{ white-space: pre-line; }}
  input[type=range] {{ width: 100%; margin: .5rem 0 0; accent-color: #4a6fa5; }}
  .unset input[type=range] {{ opacity: .4; accent-color: #999; }}
  .quick {{ display: flex; gap: .4rem; }}
  .quick button {{ flex: 1; padding: .35rem; border: 1px solid #bbb; border-radius: .4rem; background: #fafafa; cursor: pointer; }}
  .readout {{ display: flex; justify-content: space-between; align-items: center; margin-top: .3rem; min-height: 1.6rem; font-weight: bold; }}
  .readout .clear {{ border: 0; background: none; color: #666; text-decoration: underline; cursor: pointer; font-weight: normal; }}
  .unset .readout .value {{ color: #999; font-weight: normal; }}
  footer {{ padding: 0 1rem 1rem; font-size: .8rem; color: #666; }}
</style></head><body>
<header>
  <p><b>Weak, balanced, or powerful, for its mana cost?</b> Score each card from 0 (weak) through 1 (balanced) to 2 (powerful). Use the slider for in-between cards. Your scores are remembered in this browser. Paste the text below into <code>labels.txt</code>.</p>
  <textarea id="out" readonly></textarea>
  <button id="copy">Copy</button>
</header>
<main>
{cards}
</main>
<footer>Card images and text from Scryfall. Card names, art, and text belong to Wizards of the Coast.</footer>
<script>
  const names = {names};
  const fromFile = {from_file};  // scores already in labels.txt
  const out = document.getElementById("out");
  const key = n => "spell-power-score:" + n;
  const oldKey = n => "spell-power:" + n;  // the first version of this page stored words
  const oldWords = {{weak: 0, balanced: 1, powerful: 2}};
  const words = ["weak", "balanced", "powerful"];
  const stored = n => {{
    const v = localStorage.getItem(key(n));
    if (v !== null) return v === "" ? null : Number(v);  // "" marks a card you cleared
    const old = localStorage.getItem(oldKey(n));
    return old in oldWords ? oldWords[old] : null;
  }};
  for (const [n, s] of Object.entries(fromFile)) if (localStorage.getItem(key(n)) === null && stored(n) === null) localStorage.setItem(key(n), String(s));  // what you already set in the browser wins, even a clear
  function render() {{
    out.value = names.map(n => (stored(n) === null ? "?" : stored(n).toFixed(1)) + " | " + n).join("\\n");
  }}
  document.querySelectorAll(".judge").forEach(box => {{
    const name = box.dataset.card, slider = box.querySelector("input[type=range]");
    const value = box.querySelector(".value");
    function show(v) {{
      box.classList.toggle("unset", v === null);
      if (v === null) {{ slider.value = 1; value.textContent = "not judged yet"; return; }}
      slider.value = v;
      value.textContent = v.toFixed(1) + " \\u00b7 " + words[Math.min(Math.max(Math.round(v), 0), 2)];
    }}
    function set(v) {{ localStorage.setItem(key(name), String(v)); show(v); render(); }}
    slider.addEventListener("input", () => set(Number(slider.value)));
    box.querySelectorAll(".quick button").forEach(b => b.addEventListener("click", () => set(Number(b.dataset.score))));
    box.querySelector(".clear").addEventListener("click", () => {{
      localStorage.setItem(key(name), ""); localStorage.removeItem(oldKey(name)); show(null); render();
    }});
    show(stored(name));
  }});
  document.getElementById("copy").addEventListener("click", () => {{ out.select(); document.execCommand("copy"); }});
  render();
</script></body></html>
"""


def _card_html(card: Card) -> str:
    name = html.escape(card.name)
    image = f'<img src="{html.escape(card.image_url)}" alt="{name}" loading="lazy">' if card.image_url else ""
    stats = f" {html.escape(card.power)}/{html.escape(card.toughness)}" if card.power is not None and card.toughness is not None else ""
    quick = "".join(f'<button type="button" data-score="{p.value}">{p.label}</button>' for p in Power)
    return (
        f'<section class="card">{image}'
        f'<div class="facts"><b>{name}</b> {html.escape(card.mana_cost)} (mana value {int(card.mana_value)})<br>'
        f'{html.escape(card.type_line)}{stats}<div class="text">{html.escape(card.oracle_text)}</div></div>'
        f'<div class="judge unset" data-card="{name}">'
        f'<div class="quick">{quick}</div>'
        f'<input type="range" min="0" max="2" step="0.1" value="1" aria-label="Score for {name}">'
        f'<div class="readout"><span class="value">not judged yet</span><button type="button" class="clear">clear</button></div>'
        f"</div></section>"
    )


def _script_json(value) -> str:
    return json.dumps(value).replace("</", "<\\/")  # json.dumps is safe inside <script> only with "</" escaped


def cards_page(cards: list[Card], chosen: dict[str, float]) -> str:
    """`chosen` holds the scores already in labels.txt; the page starts from them for any card you haven't touched in this browser."""
    return PAGE.format(
        cards="\n".join(_card_html(c) for c in cards),
        names=_script_json([c.name for c in cards]),
        from_file=_script_json(chosen),
    )
