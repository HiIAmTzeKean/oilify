# Oilify

A fresh application shell for the Oilify frontend and backend.

![landing_page](/static/LandingPage.png)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/HiIAmTzeKean/RecNextEval-Studio.git
   ```

2. Navigate to the Oilify workspace directory:
   ```bash
   cd oilify
   ```

3. No external RecNextEval checkout is required anymore. The backend is now a minimal Oilify API and the frontend is a clean landing shell.

## Running the Application

To start the entire server stack (PostgreSQL database, backend API, and frontend), run:

```bash
make up
```

This will:
- Start the backend API server on port 9000
- Start the frontend development server on port 8000

You can then access the application at `http://localhost:8000` and the backend health check at `http://localhost:9000/health`.
