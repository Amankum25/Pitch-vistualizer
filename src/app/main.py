import os
import pathlib
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

from src.app.api.v1.endpoints import router as api_router

OUTPUTS_DIR = pathlib.Path("outputs")
FRONTEND_DIR = pathlib.Path("frontend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure outputs directory exists
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown (nothing to clean up)


app = FastAPI(
    title="Pitch Visualizer API",
    version="2.0.0",
    description="Convert narrative text into comic-style storyboards.",
    lifespan=lifespan,
)

# CORS
cors_origin = os.getenv("CORS_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix="/api/v1")

# Serve frontend as static files
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
