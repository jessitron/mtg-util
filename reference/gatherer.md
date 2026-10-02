# Gatherer (Wizards' card database)

Site: https://gatherer.wizards.com. No API; we only link to it. Checked in Chrome on 2026-10-02.

## Linking to a card by name
- Quick search (the top search box): `https://gatherer.wizards.com/search?searchTerm=<name>`. Encode spaces as `%20` (the site itself writes `_`; both work). Commas and hyphens work.
- Use the **front-face name** for two-faced cards. `Front // Back` is Scryfall's naming, not what you'd type.
- The result is a list (one card for every prepared card we tried), so a link costs the reader one more click.
- Don't use `advanced-search?name=...`. It ignores the parameter and opens an empty form.
- The Gatherer page is a JS app. `curl` returns 200 for any URL, so check links in a browser.

## Linking straight to a card page
- Card pages look like `/<SET>/en-us/<collector-number>/<slug>`, e.g. `/SOS/en-us/162/studious-first-year`.
- Scryfall has `set` and `collector_number` for this. Not built into prepared-cards; it would mean two more fields on `Card` and a cache refresh.

## Gotchas
- Scryfall's `related_uris.gatherer` and `multiverse_ids` are empty for new cards. None of the 75 `o:prepared` cards had them on 2026-10-02, so we can't use Scryfall's own Gatherer link.
- Search-result tiles can show a blank frame with just the name while the image loads; the detail page is fine.
