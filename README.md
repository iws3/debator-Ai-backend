<img width="1083" height="713" alt="image" src="https://github.com/user-attachments/assets/739a0cca-a84b-4eb7-9bef-2e525db56557" />


# Debator

A real-time debate AI in Nigerian Pidgin English.

## Project Structure

- `backend/`: FastAPI backend with Google Gemini and YarnGPT integration.
- `frontend/`: (Coming soon) Frontend application.

## Backend Setup

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```

2.  Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Set up environment variables:
    - Copy `.env.example` to `.env`
    - Fill in your `YARNGPT_API_KEY` and `GOOGLE_API_KEY`.

5.  Run the server:
    ```bash
    uvicorn main:app --reload
    ```

## Deployment on Render

1.  Push this repository to GitHub/GitLab.
2.  Create a new **Web Service** on Render.
3.  Connect your repository.
4.  Render should automatically detect the `render.yaml` file (or you can manually configure it).
    - **Build Command**: `pip install -r requirements.txt`
    - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5.  Add your Environment Variables in the Render dashboard:
    - `YARNGPT_API_KEY`
    - `GOOGLE_API_KEY`
