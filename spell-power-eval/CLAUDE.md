# spell-power-eval

Notes for working in this directory. Usage is in [README.md](README.md).

## Paid API

- **Keys live in an untracked `.be` file at the repo root** (`export NAME=...` lines; globally git-ignored). Run `source .be` before a run that calls a paid API. Never print the values; list names only (`sed -E 's/=.*/=<redacted>/' .be`).
- **A run that spends money gets a free `--dry-run`, and its first real run uses one card.** Ask Jess before any run that costs more than cents.

## Checking the results page in a browser

- **Chrome (the claude-in-chrome tools) refuses `file://` URLs.** Serve over http on a throwaway port. For the results page, run the real server from the worktree: `PORT=8791 ./run --serve` (the port is an environment variable; there is no `--port` flag). It reads the HTML on each request, so edits show on refresh. For a static page, use `python3 -m http.server <port> --bind 127.0.0.1` from a temp directory. `--serve` defaults to 8780 and Jess runs another server on 8799, so pick a different port and check it is free first (`lsof -i :<port>`).
- **Afterward:** clear `localStorage` on that origin, close the tab, delete any fixture or copy, and stop the server. `pkill -f` on the command line did not find it; use `lsof -ti :<port> -sTCP:LISTEN` and kill that pid, then check the port is quiet.
- **Test a sort or render change by reading the DOM.** `javascript_tool` can click a control and return the card names in row order (`#where .grid-row:not(.grid-head) .name`) next to `state.run`, which shows the order is right without a screenshot.
- **Page tests with fixtures.** Copy `tests/fixtures/sample_run.json` into `results/` under a throwaway *timestamp-style* name such as `29991231T000000Z.json` (the server lists only those; `zz-x.json` is silently missing from the menu), then delete it. The fixture has costs; the real run in `results/` predates cost tracking and shows dashes. Never run a paid arm just to get data.

## Design

- **Show people what the model sees.** Build each request in one function that both the classifier and any page call, so the page can't drift from what is sent.

## Honeycomb

Team `modernity`, environment `local`, dataset `spell-power-eval`. Call `get_dataset_columns` before `run_query`, because column names are namespaced and a missing one fails the query. Read-only checks send no data. What arrives, and the quirks, are in [../reference/honeycomb.md](../reference/honeycomb.md).
