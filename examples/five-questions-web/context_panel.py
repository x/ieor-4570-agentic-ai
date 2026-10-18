"""A side panel that shows the context: the exact message list sent to the model each turn.

To add it to a web agent that keeps a `sessions` dict:
    app.py:      add_context_panel(app, sessions)
    index.html:  <script src="/context-panel.js"></script>
                 then call showContext(sessionId) whenever the session changes
Delete those lines to remove it.
"""

from pathlib import Path

from fastapi.responses import FileResponse


def add_context_panel(app, sessions):
    @app.get("/context")
    def context(session_id: str):
        return sessions.get(session_id, [])

    @app.get("/context-panel.js")
    def script():
        return FileResponse(Path(__file__).parent / "context-panel.js")
