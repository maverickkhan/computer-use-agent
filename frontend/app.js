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

  // First, save the message via POST
  fetch(
    `/sessions/${selectedSession}/messages?text=${encodeURIComponent(text)}`,
    {
      method: "POST",
    }
  )
    .then((res) => {
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      return res.json();
    })
    .then((result) => {
      console.log("Message saved, connecting to WebSocket for streaming response...");
      // Now connect to WebSocket to get streaming response
      connectProgressStream(selectedSession);
    })
    .catch((error) => {
      console.error("Error:", error);
      appendChat(`Error: ${error.message}`, "error");
    });
}

function appendChat(text, role) {
  console.log("🚀 ~ appendChat called with:", { text: text.substring(0, 50) + "...", role });
  const chat = document.getElementById("chatHistory");
  const div = document.createElement("div");
  div.textContent = text;
  div.className = role === "user" ? "user-msg" : "bot-msg";
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  console.log("🚀 ~ Message added to chat. Total messages:", chat.children.length);
}

// =============== PROGRESS STREAM (WebSocket) ===============

// function connectProgressStream(sessionId) {
//     if (ws) ws.close();
//     ws = new WebSocket(`ws://${location.hostname}:8000/sessions/${sessionId}/stream`);
//     ws.onmessage = e => appendChat("[progress] " + e.data, "bot-msg");
//     ws.onclose = () => console.log("Progress stream closed");
// }

function connectProgressStream(sessionId) {
  console.log("🚀 ~ connectProgressStream ~ sessionId:", sessionId)
  if (ws) ws.close();
  ws = new WebSocket(
    `ws://${location.hostname}:8080/sessions/${sessionId}/stream`
  );
  
  ws.onopen = () => {
    console.log("🚀 ~ WebSocket connection opened successfully");
  };
  
  ws.onmessage = (e) => {
    console.log("🚀 ~ WebSocket message received:", e.data);
    console.log("🚀 ~ Message length:", e.data.length);
    try {
      const block = JSON.parse(e.data);
      console.log("🚀 ~ Parsed block:", block);
      console.log("🚀 ~ Block type:", block.type);
      
      if (block.type === "text" && block.text) {
        console.log("🚀 ~ Displaying text block:", block.text);
        appendChat("Agent: " + block.text, "agent");
      } else if (block.type === "tool_use") {
        console.log("🚀 ~ Displaying tool_use block:", block.name);
        appendChat(`Agent: [Running tool: ${block.name}]`, "agent");
      } else if (block.type === "tool_result") {
        console.log("🚀 ~ Displaying tool_result block:", block.result);
        console.log("🚀 ~ Tool result keys:", Object.keys(block.result));
        console.log("🚀 ~ Tool result base64_image exists:", !!block.result.base64_image);
        displayToolResult(block.result, block.tool_use_id);
      } else if (block.type === "error") {
        console.log("🚀 ~ Displaying error block:", block.message);
        appendChat(`Error: ${block.message}`, "error");
      } else if (block.type === "complete") {
        console.log("🚀 ~ Agent task completed");
        appendChat("Agent: [Task completed]", "agent");
      } else {
        console.log("🚀 ~ Unknown block type:", block.type);
      }
    } catch (error) {
      console.error("🚀 ~ Error parsing WebSocket message:", error);
      console.error("🚀 ~ Raw message data:", e.data);
    }
  };
  
  ws.onerror = (error) => {
    console.error("🚀 ~ WebSocket error:", error);
    appendChat("Error: WebSocket connection failed", "error");
  };
  
  ws.onclose = (event) => {
    console.log("🚀 ~ WebSocket connection closed. Code:", event.code, "Reason:", event.reason);
  };
}

function displayToolResult(result, toolUseId) {
  console.log("🚀 ~ displayToolResult called with:", { result, toolUseId });
  console.log("🚀 ~ Result keys:", Object.keys(result));
  console.log("🚀 ~ base64_image length:", result.base64_image ? result.base64_image.length : "undefined");
  console.log("🚀 ~ base64_image preview:", result.base64_image ? result.base64_image.substring(0, 50) + "..." : "undefined");
  
  const chat = document.getElementById("chatHistory");
  const div = document.createElement("div");
  div.className = "bot-msg";
  
  // Create content container
  const contentDiv = document.createElement("div");
  contentDiv.className = "tool-result-content";
  
  // Add tool ID info
  const toolInfo = document.createElement("div");
  toolInfo.className = "tool-info";
  toolInfo.textContent = `Tool Result (${toolUseId})`;
  contentDiv.appendChild(toolInfo);
  
  // Add output text if available
  if (result.output && result.output.trim()) {
    const outputDiv = document.createElement("div");
    outputDiv.className = "tool-output";
    outputDiv.textContent = result.output;
    contentDiv.appendChild(outputDiv);
  }
  
  // Add error if available
  if (result.error && result.error.trim()) {
    const errorDiv = document.createElement("div");
    errorDiv.className = "tool-error";
    errorDiv.textContent = `Error: ${result.error}`;
    contentDiv.appendChild(errorDiv);
  }
  
  // Add image if available
  if (result.base64_image) {
    console.log("🚀 ~ Displaying image from tool result");
    console.log("🚀 ~ Image data URL:", `data:image/png;base64,${result.base64_image}`);
    
    const imgDiv = document.createElement("div");
    imgDiv.className = "tool-image";
    
    const img = document.createElement("img");
    img.src = `data:image/png;base64,${result.base64_image}`;
    img.alt = "Tool result image";
    img.style.maxWidth = "100%";
    img.style.height = "auto";
    img.style.border = "1px solid #ccc";
    img.style.borderRadius = "4px";
    img.style.marginTop = "8px";
    
    // Add error handling for image loading
    img.onload = () => {
      console.log("🚀 ~ Image loaded successfully");
    };
    
    img.onerror = (error) => {
      console.error("🚀 ~ Image failed to load:", error);
      console.error("🚀 ~ Image src:", img.src);
    };
    
    imgDiv.appendChild(img);
    contentDiv.appendChild(imgDiv);
  } else {
    console.log("🚀 ~ No base64_image found in result");
  }
  
  div.appendChild(contentDiv);
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  console.log("🚀 ~ Tool result added to chat. Total messages:", chat.children.length);
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

document.getElementById('msgInput').addEventListener('keydown', function (e) {
  if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevent newline
      sendMessage();      // Send the message
  }
});
document.getElementById('msgInput').addEventListener('input', function () {
  this.style.height = 'auto';
  this.style.height = this.scrollHeight + 'px';
});
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
