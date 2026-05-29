# EventMesh

EventMesh is a full-stack application featuring a React + Vite frontend and a FastAPI (Python) backend. The project is organized into two separate directories for frontend and backend components.

## Prerequisites

Make sure you have the following installed on your system:
- **Node.js** (v16+ recommended) and **npm**
- **Python** (3.8+ recommended)
- **Docker** and **Docker Compose** (optional, but recommended for the backend database/setup)

## Project Structure

- `/frontend` - Contains the React application built with Vite.
- `/backend` - Contains the REST API built with FastAPI.

## Getting Started from Scratch

### 1. Setting up the Backend

Navigate to the `backend` directory and set up the Python application.

```bash
cd backend
```

#### Option A: Using Docker (Recommended)
1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Run the backend services using Docker Compose:
   ```bash
   docker-compose up --build
   ```

#### Option B: Manual Setup
1. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your environment variables (copy `.env.example` to `.env` and configure `DATABASE_URL` with your PostgreSQL instance).
4. Run the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

The backend server will be available at `http://localhost:8000`.

### 2. Setting up the Frontend

Open a new terminal window, navigate to the `frontend` directory, and start the development server.

```bash
cd frontend

# Install Node.js dependencies
npm install

# Start the Vite development server
npm run dev
```

The frontend application will be available at `http://localhost:5173`.
