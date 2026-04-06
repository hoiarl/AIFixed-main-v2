from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.routes import file_routes, presentation_routes, test_routes
from src.preload import preload_models

app = FastAPI(
    title="API Documentation",
    description="API documentation for the service",
    version="1.0.0",
    root_path="/api",
    docs_url="/docs",
)

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Set-Cookie",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Origin",
        "Authorization",
        "X-Telegram-User-ID",
        "x-telegram-id",
    ],
)


@app.on_event("startup")
async def startup_event():
    logging.info("Starting up - preloading models...")
    try:
        preload_models()
        logging.info("✓ Models preloaded successfully")
    except Exception as e:
        logging.error(f"Failed to preload models: {e}")
        raise


app.include_router(presentation_routes.router)
app.include_router(file_routes.router)
app.include_router(test_routes.router)
