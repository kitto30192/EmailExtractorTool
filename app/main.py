import sys
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, extract

# This forces the Uvicorn child process to use the correct Windows engine for Playwright
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(title="Email Extractor API")

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
   "https://email-extractor-tool-mocha.vercel.app" 
    # Add your deployed frontend URL here when going live!
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(extract.router)

@app.get("/")
def read_root():
    return {"message": "API is running. Ready for extraction!"}