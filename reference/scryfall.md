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

## Fields for judging cards
- `edhrec_rank`: popularity among Commander decks; lower is more popular (Sol Ring was 1 on 2026-10-02). Absent on cards EDHREC doesn't rank.
- `power`, `toughness`, `loyalty` are strings (`"*"` happens). On two-faced cards they sit in `card_faces[n]`, as do `mana_cost` and `oracle_text`.
