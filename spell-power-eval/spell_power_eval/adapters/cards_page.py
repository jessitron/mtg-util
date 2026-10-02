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
  .choices {{ display: flex; gap: .4rem; }}
  .choices label {{ flex: 1; text-align: center; padding: .45rem; border: 2px solid #ccc; border-radius: .4rem; cursor: pointer; }}
  .choices input {{ display: none; }}
  .choices input:checked + span {{ font-weight: bold; }}
  .choices label:has(input:checked) {{ color: #fff; border-color: transparent; }}
  .choices label.weak:has(input:checked) {{ background: #b5533c; }}
  .choices label.balanced:has(input:checked) {{ background: #6b7b8c; }}
  .choices label.powerful:has(input:checked) {{ background: #2f7d4f; }}
  footer {{ padding: 0 1rem 1rem; font-size: .8rem; color: #666; }}
</style></head><body>
<header>
  <p><b>Weak, balanced, or powerful, for its mana cost?</b> Pick one per card. Your picks are remembered in this browser. Paste the text below into <code>labels.txt</code>.</p>
  <textarea id="out" readonly></textarea>
  <button id="copy">Copy</button>
</header>
<main>
{cards}
</main>
<footer>Card images and text from Scryfall. Card names, art, and text belong to Wizards of the Coast.</footer>
<script>
  const names = {names};
  const out = document.getElementById("out");
  const key = n => "spell-power:" + n;
  function render() {{
    out.value = names.map(n => (localStorage.getItem(key(n)) || "?") + " | " + n).join("\\n");
  }}
  document.querySelectorAll("input[type=radio]").forEach(r => {{
    if (localStorage.getItem(key(r.dataset.card)) === r.value) r.checked = true;
    r.addEventListener("change", () => {{ localStorage.setItem(key(r.dataset.card), r.value); render(); }});
  }});
  document.getElementById("copy").addEventListener("click", () => {{ out.select(); document.execCommand("copy"); }});
  render();
</script></body></html>
"""


def _card_html(card: Card, chosen: "Power | None") -> str:
    name = html.escape(card.name)
    image = f'<img src="{html.escape(card.image_url)}" alt="{name}" loading="lazy">' if card.image_url else ""
    stats = f" {html.escape(card.power)}/{html.escape(card.toughness)}" if card.power is not None and card.toughness is not None else ""
    buttons = "".join(
        f'<label class="{p.label}"><input type="radio" name="{name}" value="{p.label}" data-card="{name}"'
        f'{" checked" if p == chosen else ""}><span>{p.label}</span></label>'
        for p in Power
    )
    return (
        f'<section class="card">{image}'
        f'<div class="facts"><b>{name}</b> {html.escape(card.mana_cost)} (mana value {int(card.mana_value)})<br>'
        f'{html.escape(card.type_line)}{stats}<div class="text">{html.escape(card.oracle_text)}</div></div>'
        f'<div class="choices">{buttons}</div></section>'
    )


def cards_page(cards: list[Card], chosen: dict[str, Power]) -> str:
    # json.dumps output is safe inside <script> only with "</" escaped
    names = json.dumps([c.name for c in cards]).replace("</", "<\\/")
    return PAGE.format(cards="\n".join(_card_html(c, chosen.get(c.name)) for c in cards), names=names)
