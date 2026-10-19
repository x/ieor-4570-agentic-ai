// Context panel: shows the message list the server sends to the model on every turn.
// Include with <script src="/context-panel.js"></script>, then call showContext(sessionId).

const contextStyle = document.createElement("style");
contextStyle.textContent = `
    body { margin-right: min(40vw, 32rem); }
    #context-panel {
        position: fixed; top: 0; right: 0; bottom: 0;
        width: min(40vw, 32rem);
        overflow-y: auto;
        padding: 1.5rem;
        background: #fafafa;
        border-left: 1px solid #e0e0e0;
        font-family: ui-monospace, monospace;
        font-size: 0.75rem;
    }
    #context-panel h2 {
        font-family: system-ui, sans-serif;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #999;
        margin-bottom: 1rem;
    }
    .context-msg {
        border-left: 3px solid #999;
        padding: 0.4rem 0.75rem;
        margin-bottom: 0.5rem;
        white-space: pre-wrap;
        word-break: break-word;
    }
    .context-msg .role { font-weight: bold; }
    .context-msg.system { border-color: #dc2626; }
    .context-msg.user { border-color: #16a34a; }
    .context-msg.assistant { border-color: #2563eb; }
    .context-msg.tool { border-color: #f59e0b; }
    .context-msg.new { animation: context-flash 1.5s; }
    .context-msg .dropped { color: #aaa; font-style: italic; margin: 0.25rem 0; }
    @keyframes context-flash { from { background: #fef3c7; } }
    @media (max-width: 800px) {
        body { margin-right: 0; height: auto !important; flex-direction: column; }
        #context-panel { position: static; width: 100%; border-left: none; }
    }
`;
document.head.appendChild(contextStyle);

const contextPanel = document.createElement("aside");
contextPanel.id = "context-panel";
document.body.appendChild(contextPanel);
let contextShown = 0;

async function showContext(sessionId) {
    const res = await fetch("/context?session_id=" + encodeURIComponent(sessionId));
    const messages = await res.json();

    contextPanel.innerHTML = "<h2>Context (" + messages.length + " messages)</h2>";
    messages.forEach((m, i) => {
        const div = document.createElement("div");
        // Highlight what this turn added
        div.className = "context-msg " + m.role + (i >= contextShown ? " new" : "");
        const role = document.createElement("div");
        role.className = "role";
        role.textContent = m.role;
        div.appendChild(role);
        // Hidden thinking is shown but grayed out: it isn't sent back to the model next turn
        if (m.thinking) {
            const thinking = document.createElement("div");
            thinking.className = "dropped";
            thinking.textContent = "thinking (not sent back to the model):\n" + m.thinking;
            div.appendChild(thinking);
        }
        // Tool-call turns have no text, so show the calls instead
        div.appendChild(
            document.createTextNode(m.content ?? JSON.stringify(m.tool_calls, null, 2)),
        );
        contextPanel.appendChild(div);
    });
    contextShown = messages.length;
    contextPanel.scrollTop = contextPanel.scrollHeight;
}
