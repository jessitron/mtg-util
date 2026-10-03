# prepared-cards

Notes for working in this directory. Usage is in [README.md](README.md).

- **Test against a throwaway server.** Don't POST to Jess's running server or touch her `selected.txt`; start another copy with `PORT=<other> ./run` (it kills only the server on its own port). The default port is 8765, and Jess runs another server on 8799. Check that your port is free first (`lsof -i :<port>`), and stop the server afterward.
- **Chrome (the claude-in-chrome tools) refuses `file://` URLs.** Serve over http, as the throwaway server does. Afterward: clear `localStorage` on that origin and close the tab.
- **Run the tests with `uv run`** (`uv run python -m unittest discover -s tests -t .`). The LLM adapter imports `pydantic` (it comes with `anthropic`), so plain `python3` fails.
- **A real scorer needs keys and costs money.** `./run` does not source `.be`, and a worktree session refuses `source`. Use a tiny launcher outside the repo (in `$CLAUDE_JOB_DIR/tmp`) that reads `ANTHROPIC_API_KEY` / `TYPESAFE_API_KEY` from `../.be` into `os.environ`, sets `PORT` and `POWER_MODEL`, and `runpy`s `main.py`; never print the values. Measured on all 75 `o:prepared` cards (2026-10-03): Jev 13 s and $0.0015, Haiku 118 s and $0.063.
- **A worktree has no scryfall cache or score files** (they are gitignored). Copy `scryfall-cache.json` from the main checkout, or the first load refetches 75 cards from Scryfall. Score files written in a worktree stay there; the ones Jess's server reads are in the main checkout. Score files from before time and cost were recorded hold bare scores and show "an unknown cost".
- **The page is blank until `/api/cards` answers**, and the server handles one request at a time, so a long scoring run blocks everything else, including `/api/selection`.
