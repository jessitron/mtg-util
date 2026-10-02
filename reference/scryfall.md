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
