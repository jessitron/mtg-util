# MTGJSON

https://mtgjson.com — community-maintained card data for all of Magic, rebuilt daily. Free, no auth, no rate-limit concerns for a single download.

## Downloads we use

`https://mtgjson.com/api/v5/AllPrintings.sqlite` — every printing of every card, as a SQLite database (~690 MB, Oct 2026). Rebuilt daily; `Content-Length` and `Last-Modified` on a HEAD request tell you whether it changed.

Other formats exist (`AllPrintings.json`, `AllPrintings.sqlite.xz`, `.zip`, `.psql`, `.sql`), as do smaller sets like `AtomicCards.json` (one record per card name, no printings).

## Local copy

- **File:** `/Users/jessitron/code/jessitron/mtg-util/mtgjson/data/AllPrintings.sqlite`, fetched by `mtgjson/run`, git-ignored (so it exists only in the main checkout, not in worktrees), mode 444, 691,171,328 bytes.
- **Downloaded:** 2026-10-02 (about 16:30 local), from `https://mtgjson.com/api/v5/AllPrintings.sqlite`. Build `meta`: date 2026-10-02, version 5.3.0+20261002. Update this line after each refresh.
- **Made available:** the whole `AllPrintings` database, every table listed below. Nothing is filtered or transformed, and we added no tables, indexes, or views. It is read-only; scripts must open it with `mode=ro`.
- **Tools:** `mtgjson/bin/mtgjson-query`, `mtgjson-card`, and `mtgjson-schema` (absolute paths, work from a worktree). Usage is in [mtgjson/README.md](../mtgjson/README.md).

## Schema notes

Checked against the 2026-10-02 build (5.3.0): 114,557 `cards` rows, 35,081 distinct names.

- Tables: `cards`, `cardIdentifiers`, `cardLegalities`, `cardForeignData`, `cardRulings`, `cardPurchaseUrls`, `tokens`, `tokenIdentifiers`, `sets`, `setTranslations`, `sealedProducts`, `setDecks`, `setBooster*`, `meta`.
- `meta` holds the build `date` and `version`.
- `cards` has one row per printing (`uuid`); columns include `name`, `setCode`, `manaValue`, `manaCost`, `type`, `text`, `side` (a/b for multi-face), `faceName`, `colors`, `keywords`, `layout`, `rarity`, `edhrecRank`.
- `cardIdentifiers` (keyed by `uuid`) maps to `scryfallId`, `scryfallOracleId`, `multiverseId`, `mtgArenaId`, `mtgoId`, `tcgplayerProductId`, and more. Join on `scryfallId` to move between MTGJSON and Scryfall.
- Legalities live in `cardLegalities`, one row per card and format.
