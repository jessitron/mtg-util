# Scryfall API

Docs: https://scryfall.com/docs/api

## Search
- `GET https://api.scryfall.com/cards/search?q=<query>&order=cmc`
- Paginated: follow `next_page` while `has_more` is true (175 cards per page).
- Send `User-Agent` and `Accept` headers; wait 50-100ms between requests.
- `o:prepared` returned 75 cards on 2026-10-02.

## Card shape quirks
- Layout `prepare`: two faces, name is `Front // Back`, `cmc` is the front face's. Top-level `image_uris` is present, so no need to dig into `card_faces` (other multi-face layouts, like `transform`, put images only in `card_faces[n].image_uris`).
- `cmc` is a float (`1.0`).
- New cards have no `multiverse_ids` and no `related_uris.gatherer`. See [gatherer.md](gatherer.md).

## Look up many cards by name
- `POST https://api.scryfall.com/cards/collection` with `{"identifiers": [{"name": "Sol Ring"}, ...]}`. Up to 75 identifiers per request. One request replaces many `cards/named` calls.
- Response: `data` (card objects) and `not_found` (the identifiers it missed).
- A front-face name alone matches a two-faced card, and `data[].name` comes back as `Front // Back`.
- **A back-face name does not match** (checked 2026-10-02): `collection` lists "Unwind History" in `not_found`, and `cards/named?exact=Unwind History` is a 404.

## Find a prepared card's spell (the back face)
- Search by exact name: `GET /cards/search?q=!"Unwind History"` returns the whole card (`Diviner of Victory // Unwind History`). `!"..."` is Scryfall's exact-name operator, and it does match either face.
- To list every prepared card: `q=o:prepared layout:prepare` (70 cards on 2026-10-02; plain `o:prepared` also catches cards that only mention the word).
- The spell is `card_faces[1]`: its own `name`, `mana_cost`, `type_line` (so far Sorcery or Instant), `oracle_text`. Top-level `cmc` is the creature's, not the spell's, so work out the spell's mana value from its `mana_cost` (a number is itself, any other symbol is 1, `{X}` is 0).
- Creature faces say "This creature enters prepared. (While it's prepared, you may cast a copy of its spell. Doing so unprepares it.)" Some prepared creatures don't enter prepared; other cards in the deck grant the prepared state.

## Fields for judging cards
- `edhrec_rank`: popularity among Commander decks; lower is more popular (Sol Ring was 1 on 2026-10-02). Absent on cards EDHREC doesn't rank.
- `power`, `toughness`, `loyalty` are strings (`"*"` happens). On two-faced cards they sit in `card_faces[n]`, as do `mana_cost` and `oracle_text`.
