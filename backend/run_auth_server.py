import os

from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from backend.routers import auth_routes

load_dotenv()

app = FastAPI(title="Auth Service")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "dev-session-secret"),
    same_site="lax",
    https_only=False,  # локально по http
)


app.include_router(auth_routes.router)


# (опционально) выведем маршруты при старте — очень помогает
@app.on_event("startup")
async def _print_routes():
    for r in app.routes:
        methods = getattr(r, "methods", None)
        print("ROUTE:", r.path, methods)


# точка входа для запуска как скрипта
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
