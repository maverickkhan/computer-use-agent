# Energent AI Computer Use Agent

## Demo

Watch our demo videos to see the agent in action:

### Part 1: Basic Functionality
[![Demo Part 1](https://cdn.loom.com/sessions/thumbnails/7263bb5996334ff787b9f482eae79902-with-play.gif)](https://www.loom.com/share/7263bb5996334ff787b9f482eae79902?sid=a7cd9717-773a-476f-aec1-700c941627db)

### Part 2: Advanced Features
[![Demo Part 2](https://cdn.loom.com/sessions/thumbnails/c5c1fee045a24fdfa603e8360a9279e6-with-play.gif)](https://www.loom.com/share/c5c1fee045a24fdfa603e8360a9279e6?sid=a6ea28eb-ff37-4191-9892-777e43e22a6e)

## Setup Instructions

### 1. **Environment Variables**

- Copy the example environment file and fill in your Anthropic API key:
  ```bash
  cp .env.example .env
  ```
- Edit `.env` and set your `ANTHROPIC_API_KEY` and MinIO configuration:
  ```
  ANTHROPIC_API_KEY=sk-ant-...

  # MinIO Configuration
  MINIO_HOST=minio
  MINIO_PORT=9000
  MINIO_ACCESS_KEY=minioadmin
  MINIO_SECRET_KEY=minioadmin
  MINIO_BUCKET=screenshots
  EXTERNAL_URL=http://localhost:8080
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

3. **Run MinIO Server:**
   ```bash
   docker run -d \
     -p 9000:9000 \
     -p 9001:9001 \
     --name minio \
     -e "MINIO_ROOT_USER=minioadmin" \
     -e "MINIO_ROOT_PASSWORD=minioadmin" \
     minio/minio server /data --console-address ":9001"
   ```

4. **Run the backend:**
   ```bash
   cd app
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **(Optional) Run the frontend:**
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
   - `9000`: MinIO API
   - `9001`: MinIO Console

---

### 4. **Notes**

- The `.env` file is required for both local and Docker runs. The Dockerfile copies `.env` into the container.
- The backend will not work without a valid `ANTHROPIC_API_KEY`.
- MinIO is used for storing and serving screenshots and other binary data:
  - Default credentials: `minioadmin`/`minioadmin`
  - Access MinIO Console at [http://localhost:9001](http://localhost:9001)
  - The `screenshots` bucket is created automatically on startup
  - Images are served through nginx proxy to ensure proper URL resolution
- You can use `.env.example` as a template for your own `.env` file.

---

**Summary:**  
- Copy `.env.example` to `.env` and set your API key and MinIO configuration.
- Use a Python virtual environment for local dev, or use Docker for a full-stack environment.
- The backend and agent will not function without the API key in your `.env` file.
- MinIO handles binary data storage (screenshots, etc.) with automatic bucket creation.

---

## 📺 Demo Video

Watch a full walkthrough of the Computer Use Agent challenge, demonstrating end-to-end setup, agent actions, and the integrated web interface:

[![Watch the Demo Video](https://img.youtube.com/vi/lcPM3eZUYCE/0.jpg)](https://youtu.be/lcPM3eZUYCE)

[**Click here to watch the demo on YouTube**](https://youtu.be/lcPM3eZUYCE)
