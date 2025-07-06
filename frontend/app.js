// =============== GLOBAL STATE ===============
let selectedSession = null;
let ws = null;

// =============== SESSION / TASKS ===============

// Create a new chat session
// function startNewTask() {
//   fetch("/sessions/", { method: "POST" })
//     .then((res) => res.json())
//     .then((data) => {
//       selectedSession = data.session_id;
//       loadTaskHistory();
//       loadChatHistory(selectedSession);
//       connectProgressStream(selectedSession);
//     });
// }

// List all sessions
// function loadTaskHistory() {
//   fetch("/sessions/")
//     .then((res) => res.json())
//     .then((sessions) => {
//       const taskHistory = document.getElementById("taskHistory");
//       taskHistory.innerHTML = "";
//       sessions.forEach((session) => {
//         const div = document.createElement("div");
//         div.textContent = `Session ${session.session_id}`;
//         div.className = "task-item";
//         div.onclick = () => {
//           selectedSession = session.session_id;
//           loadChatHistory(selectedSession);
//           connectProgressStream(selectedSession);
//         };
//         taskHistory.appendChild(div);
//       });
//     });
// }

function loadTaskHistory() {
    fetch("/sessions/")
        .then(res => res.json())
        .then(sessions => {
            console.log("Loaded sessions:", sessions);
            console.log("Current selectedSession BEFORE:", selectedSession);
            // If no session is selected or selected session doesn't exist, select the newest
            if (!selectedSession || !sessions.some(s => s.session_id === selectedSession)) {
                if (sessions.length > 0) {
                    selectedSession = sessions[sessions.length - 1].session_id;
                    console.log("Auto-selected newest session:", selectedSession);
                }
            }
            renderTaskList(sessions);
            // Load chat for selected session if we have one
            if (selectedSession) {
                console.log("Loading chat for session:", selectedSession);
                loadChatHistory(selectedSession);
            }
        });
}

function renderTaskList(sessions) {
    console.log("Rendering task list. Selected session:", selectedSession);
    const taskHistory = document.getElementById("taskHistory");
    taskHistory.innerHTML = "";
    sessions.forEach(session => {
        const div = document.createElement("div");
        div.textContent = `Session ${session.session_id}`;
        div.className = "task-item";
        if (selectedSession === session.session_id) {
            div.classList.add("selected-session");
        }
        div.onclick = () => {
            selectedSession = session.session_id;
            console.log("Clicked and selected session:", selectedSession);
            loadChatHistory(selectedSession);
            renderTaskList(sessions); // Re-render to update highlights
        };
        taskHistory.appendChild(div);
    });
}

function startNewTask() {
    fetch("/sessions/", { method: "POST" })
        .then(res => res.json())
        .then(data => {
            selectedSession = data.session_id;
            console.log("Created new session, set selectedSession to:", selectedSession);
            loadTaskHistory();
        });
}

function initializeApp() {
    console.log("Initializing app");
    loadTaskHistory(); // This will select the newest session and load its chat
}


// =============== CHAT / MESSAGES ===============

function loadChatHistory(sessionId) {
  fetch(`/sessions/${sessionId}`)
    .then((res) => res.json())
    .then((session) => {
      const chat = document.getElementById("chatHistory");
      chat.innerHTML = "";
      session.messages.forEach((m) => {
        appendChat(
          `${m.role === "user" ? "You" : "Agent"}: ${m.content}`,
          m.role
        );
      });
    });
}

// Send a message to the agent
function sendMessage() {
  if (!selectedSession) {
    alert("Start or select a session first.");
    return;
  }
  const msgInput = document.getElementById("msgInput");
  const text = msgInput.value.trim();
  if (!text) return;
  msgInput.value = "";

  appendChat(`You: ${text}`, "user");

  // Backend expects text as a query param (not JSON), so send as FormData
  const data = new URLSearchParams();
  data.append("text", text);

  // fetch(`/sessions/${selectedSession}/messages`, {
  //     method: "POST",
  //     headers: { "Content-Type": "application/x-www-form-urlencoded" },
  //     body: data
  // })
  fetch(
    `/sessions/${selectedSession}/messages?text=${encodeURIComponent(text)}`,
    {
      method: "POST",
    }
  )
    .then((res) => res.json())
    .then((result) => {
      appendChat(`Agent: ${result.agent_message.content}`, "agent");
    });
}

function appendChat(text, role) {
  const chat = document.getElementById("chatHistory");
  const div = document.createElement("div");
  div.textContent = text;
  div.className = role === "user" ? "user-msg" : "bot-msg";
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

// =============== PROGRESS STREAM (WebSocket) ===============

// function connectProgressStream(sessionId) {
//     if (ws) ws.close();
//     ws = new WebSocket(`ws://${location.hostname}:8000/sessions/${sessionId}/stream`);
//     ws.onmessage = e => appendChat("[progress] " + e.data, "bot-msg");
//     ws.onclose = () => console.log("Progress stream closed");
// }

function connectProgressStream(sessionId) {
  if (ws) ws.close();
  ws = new WebSocket(
    `ws://${location.hostname}:8000/sessions/${sessionId}/stream`
  );
  ws.onmessage = (e) => {
    try {
      const block = JSON.parse(e.data);
      if (block.type === "text") {
        appendChat("Agent: " + block.text, "agent");
      } else if (block.type === "tool_use") {
        appendChat(`Agent: [Running tool: ${block.name}]`, "agent");
      } else {
        appendChat(`[progress] ${e.data}`, "bot-msg");
      }
    } catch (err) {
      appendChat("[progress] " + e.data, "bot-msg");
    }
  };
  ws.onclose = () => console.log("Progress stream closed");
}

// =============== VNC VIEWER ===============

window.onload = function () {
  // Attach noVNC to proxy endpoint (through FastAPI)
  // const vncUrl = `ws://${location.hostname}:8000/vnc/websockify`;
  // const vncUrl = "ws://localhost:6080/websockify";
//   const vncUrl = `ws://${location.hostname}:8080/vnc/websockify`;
//   const vncContainer = document.getElementById("vncContainer");
//   window.rfb = new window.RFB(vncContainer, vncUrl, {
//     credentials: { password: "" },
//   });
//   window.rfb.scaleViewport = true;
//   window.rfb.viewOnly = false;

  // Load initial task list and create session if needed
//   loadTaskHistory();
//   startNewTask();
initializeApp();
// loadTaskHistory();
};

// =============== FILE UPLOAD ===============
function uploadFile() {
  const fileInput = document.getElementById("fileInput");
  if (!fileInput.files.length) return;
  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);
  fetch("/api/upload", { method: "POST", body: formData }).then(() =>
    appendChat("File uploaded: " + file.name, "user")
  );
}
