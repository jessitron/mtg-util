# spell-power-eval

Notes for working in this directory. Usage is in [README.md](README.md).

## Paid API

- **Keys live in an untracked `.be` file at the repo root** (`export NAME=...` lines; globally git-ignored). Run `source .be` before a run that calls a paid API. Never print the values; list names only (`sed -E 's/=.*/=<redacted>/' .be`).
- **A run that spends money gets a free `--dry-run`, and its first real run uses one card.** Ask Jess before any run that costs more than cents.

## Checking the results page in a browser

- **Chrome (the claude-in-chrome tools) refuses `file://` URLs.** Serve a copy over http on a throwaway port (`python3 -m http.server <port> --bind 127.0.0.1` from a temp directory). `--serve` defaults to 8780 and Jess runs another server on 8799, so pick a different port and check it is free first (`lsof -i :<port>`). Afterward: clear `localStorage` on that origin, close the tab, stop the server, delete the copy.
- **Page tests with fixtures.** Copy `tests/fixtures/sample_run.json` into `results/` under a throwaway *timestamp-style* name such as `29991231T000000Z.json` (the server lists only those; `zz-x.json` is silently missing from the menu), then delete it. The fixture has costs; the real run in `results/` predates cost tracking and shows dashes. Never run a paid arm just to get data.

## Design

- **Show people what the model sees.** Build each request in one function that both the classifier and any page call, so the page can't drift from what is sent.

## Honeycomb

Team `modernity`, environment `local`, dataset `spell-power-eval`. Call `get_dataset_columns` before `run_query`, because column names are namespaced and a missing one fails the query. Read-only checks send no data. What arrives, and the quirks, are in [../reference/honeycomb.md](../reference/honeycomb.md).
