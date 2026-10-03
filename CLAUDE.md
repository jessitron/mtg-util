# mtg-util

A collection of MTG-related utility scripts, plus accumulated knowledge about Scryfall, Archidekt, and related APIs.

## Layout

- `README.md`: top-level index. Lists every script with a one-line description.
- `<script-name>/`: one directory per script, each with its own `README.md`. A script's working notes (keys, ports, test procedures) go in its own `CLAUDE.md`, which loads only when you work there.
- `reference/`: API notes and resource docs (one file per API or resource; indexed in `reference/README.md`).

## Conventions

- **Every script gets a directory and a README.** When you add one, also add it to the table in the main `README.md`.
- **Capture API knowledge.** When you learn something about an API (endpoint shape, rate limit, auth, quirk), write it in `reference/` rather than leaving it in a script comment or in your head. Link to it from the script's README.
- **Top-level `./run`.** If a script needs a launcher, keep it simple and document it in that script's README.
- **Be a good API citizen.** Send the headers, pace requests, use bulk data for large jobs, and cache locally. Scryfall's specifics are in [reference/scryfall.md](reference/scryfall.md).
- **Verify outside links in a browser.** Gatherer and similar JS apps answer 200 to any URL, so `curl` proves nothing ([reference/gatherer.md](reference/gatherer.md)).
- **No secrets in the repo.** API keys live in an untracked `.be` file at the repo root; never print the values. Details are in the script that needs them.
- **Browser checks need http.** Chrome (the claude-in-chrome tools) refuses `file://`, so serve a copy on a throwaway port. Ports taken: 8765 prepared-cards, 8780 spell-power-eval `--serve`, 8799 Jess's own server. Each script's `CLAUDE.md` has the procedure.
- **Worktree sessions refuse compound shell commands.** A Bash call that mixes the word "git", `$VARS`, or a `cd` with other commands can be rejected, even inside a heredoc. Use literal paths, one plain command per call, and the Edit tool for text with such words. `CLAUDE_JOB_DIR` is `/Users/jessitron/.claude-personal/jobs/<id>`.
- **Main may move while you work in a worktree.** Rebase the worktree branch onto main (enter it with `EnterWorktree` and `path`) before the fast-forward, or the merge fails.

## Card database (mtgjson)

A local, read-only SQLite copy of every MTG card (MTGJSON's AllPrintings) lives in the main checkout. **Use it instead of calling Scryfall** when you need card text, mana value, types, legalities, or printings. Query it by absolute path, which works from a worktree:

- `/Users/jessitron/code/jessitron/mtg-util/mtgjson/bin/mtgjson-card "Lightning Bolt"` — look up one card.
- `/Users/jessitron/code/jessitron/mtg-util/mtgjson/bin/mtgjson-query "SQL"` — run any read-only SQL (`-json`, `-csv` for other formats).
- `/Users/jessitron/code/jessitron/mtg-util/mtgjson/bin/mtgjson-schema [table]` — list tables or columns.

Full usage and gotchas: [mtgjson/README.md](mtgjson/README.md). What the data holds and when it was downloaded: [reference/mtgjson.md](reference/mtgjson.md). Refresh with `mtgjson/run`, then update the download date in the reference. Never write to the database.

## Keeping docs current

- Script behavior changes → update that script's README.
- New or removed script → update the main `README.md` table.
- New API fact → update `reference/`.
