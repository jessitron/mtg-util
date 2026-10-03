# prepared-cards

Notes for working in this directory. Usage is in [README.md](README.md).

- **Test against a throwaway server.** Don't POST to Jess's running server or touch her `selected.txt`; start another copy with `PORT=<other> ./run` (it kills only the server on its own port). The default port is 8765, and Jess runs another server on 8799. Check that your port is free first (`lsof -i :<port>`), and stop the server afterward.
- **Chrome (the claude-in-chrome tools) refuses `file://` URLs.** Serve over http, as the throwaway server does. Afterward: clear `localStorage` on that origin and close the tab.
