# Energent AI Computer Use Agent

## Setup Instructions

### 1. **Environment Variables**

- Copy the example environment file and fill in your Anthropic API key:
  ```bash
  cp .env.example .env
  ```
- Edit `.env` and set your `ANTHROPIC_API_KEY`:
  ```
  ANTHROPIC_API_KEY=sk-ant-...
  ```

---

### 2. **Run Locally (Python Virtual Environment)**

1. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r computer-use-demo/computer_use_demo/requirements.txt
   ```

3. **Run the backend:**
   ```bash
   cd app
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **(Optional) Run the frontend:**
   - If you have a frontend build process, follow its instructions, or serve `frontend/index.html` with your preferred static server.

---

### 3. **Run with Docker**

1. **Build and start the container:**
   ```bash
   docker compose up --build
   ```

2. **Access the app:**
   - Open [http://localhost:8080](http://localhost:8080) in your browser.

3. **Ports:**
   - `8080`: Main entrypoint (frontend, API, noVNC, etc.)
   - `6080`: Direct noVNC access (for debugging)
   - `5900`: Native VNC client (for debugging)

---

### 4. **Notes**

- The `.env` file is required for both local and Docker runs. The Dockerfile copies `.env` into the container.
- The backend will not work without a valid `ANTHROPIC_API_KEY`.
- You can use `.env.example` as a template for your own `.env` file.

---

**Summary:**  
- Copy `.env.example` to `.env` and set your API key.
- Use a Python virtual environment for local dev, or use Docker for a full-stack environment.
- The backend and agent will not function without the API key in your `.env` file.

---

## 📺 Demo Video

Watch a full walkthrough of the Computer Use Agent challenge, demonstrating end-to-end setup, agent actions, and the integrated web interface:

[![Watch the Demo Video](https://img.youtube.com/vi/lcPM3eZUYCE/0.jpg)](https://youtu.be/lcPM3eZUYCE)

[**Click here to watch the demo on YouTube**](https://youtu.be/lcPM3eZUYCE)
