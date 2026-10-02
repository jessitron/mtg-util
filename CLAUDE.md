# mtg-util

A collection of MTG-related utility scripts, plus accumulated knowledge about Scryfall, Archidekt, and related APIs.

## Layout

- `README.md`: top-level index. Lists every script with a one-line description.
- `<script-name>/`: one directory per script, each with its own `README.md`.
- `reference/`: API notes and resource docs (one file per API or resource; indexed in `reference/README.md`).

## Conventions

- **Every script gets a directory and a README.** When you add one, also add it to the table in the main `README.md`.
- **Capture API knowledge.** When you learn something about an API (endpoint shape, rate limit, auth, quirk), write it in `reference/` rather than leaving it in a script comment or in your head. Link to it from the script's README.
- **Top-level `./run`.** If a script needs a launcher, keep it simple and document it in that script's README.
- **Be a good API citizen.** Scryfall asks for a `User-Agent` and `Accept` header, a delay of 50-100ms between requests, and use of bulk data for large jobs. Cache responses locally when practical.
- **No secrets in the repo.** Read tokens and credentials from environment variables; document the variable names in the script's README.

- **Verify outside links in a browser.** Sites like Gatherer are JS apps that answer 200 to any URL, so `curl` proves nothing. Open the link in Chrome before committing it.
- **Test against a throwaway server.** Don't POST to the user's running server or touch their `selected.txt`; start another copy with `PORT=<other> ./run` (it kills only the server on its own port).

## Keeping docs current

- Script behavior changes → update that script's README.
- New or removed script → update the main `README.md` table.
- New API fact → update `reference/`.
