import sys
import asyncio
import io
import re
import os
from urllib.parse import urlparse, urljoin
import pandas as pd
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Response, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from pydantic import BaseModel
from pymongo import MongoClient
import bcrypt
import jwt
import datetime
from dotenv import load_dotenv
import certifi
import requests

# Fix for Windows NotImplementedError when using Playwright
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Load environment variables from the .env file
load_dotenv()

app = FastAPI()

# --- CORS Configuration ---
# IMPORTANT: Must use specific origins for HttpOnly cookies to work!
origins = [
    "http://localhost:5173", 
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE SETUP ---
MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY", "your_fallback_secret_key")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")

if not MONGO_URI:
    raise ValueError("Missing MONGO_URI environment variable!")

# Connected with certifi to prevent SSL Certificate errors
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.email_extractor_db
users_collection = db.users

class User(BaseModel):
    email: str
    password: str

# --- AUTHENTICATION ROUTES ---

@app.post("/api/signup/")
async def signup(user: User):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    users_collection.insert_one({"email": user.email, "password": hashed_password})
    return {"message": "User created successfully"}

@app.post("/api/login/")
async def login(user: User, response: Response):
    db_user = users_collection.find_one({"email": user.email})
    
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials (Email not found)")
    
    # Check the password
    stored_password = db_user["password"]
    if isinstance(stored_password, str):
        stored_password = stored_password.encode('utf-8')
        
    is_password_correct = bcrypt.checkpw(user.password.encode('utf-8'), stored_password)
    
    if not is_password_correct:
        raise HTTPException(status_code=401, detail="Invalid credentials (Password mismatch)")
    
    # Generate JWT Token valid for 24 hours
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    token = jwt.encode({"sub": user.email, "exp": expiration}, SECRET_KEY, algorithm="HS256")
    
    # Set the HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,  
        max_age=86400,  
        expires=86400,
        samesite="none", 
        secure=True,   # Set to True when deploying with HTTPS
    )
    return {"message": "Login successful"}

@app.post("/api/logout/")
async def logout(response: Response):
    # The rules here must perfectly match the rules used in login()
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="none",
        secure=True
    )
    return {"message": "Logged out successfully"}

@app.get("/api/verify/")
async def verify_session(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# --- DEPENDENCY FOR PROTECTING ROUTES ---

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session")

# --- EXTRACTION LOGIC ---


async def check_pages_and_extract_async(domain: str, context, semaphore) -> str:
    """
    ASYNC Optimized version: Runs concurrently, blocks images/CSS, and uses early exits.
    """
    # 1. Skip blank rows instantly
    if pd.isna(domain) or domain.strip() == "" or domain.lower() == "nan":
        return ""

    if not domain.startswith("http"):
        domain = "https://" + domain
        
    paths_to_check = ["", "/contact", "/contact-us", "/about", "/about-us"]
    extracted_emails = set()
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    # 2. The Semaphore "Bouncer": Waits in line until one of the 10 slots opens up
    async with semaphore: 
        try:
            page = await context.new_page()
            
            # Block heavy resources instantly to save bandwidth and RAM
            await page.route("**/*", lambda route: route.abort() 
                if route.request.resource_type in ["image", "stylesheet", "media", "font", "other"] 
                else route.continue_()
            )

            for path in paths_to_check:
                target_url = urljoin(domain, path)
                print(f"  -> [Async] Checking: {target_url}")
                try:
                    # 'domcontentloaded' and 15s timeout for maximum speed
                    await page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
                    page_html = await page.content()
                    
                    matches = re.findall(email_pattern, page_html)
                    valid_emails = [
                        m for m in matches 
                        if not m.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.css', '.js', '.svg'))
                    ]
                    extracted_emails.update(valid_emails)
                    
                    if extracted_emails:
                        print(f"  -> [Async] Success! Skipping remaining pages for {domain}")
                        break
                        
                except Exception:
                    # Silently skip timeouts to keep the logs clean
                    continue
        finally:
            # ALWAYS close the tab to free up RAM, even if the scrape failed
            await page.close() 

    return ", ".join(extracted_emails)

@app.post("/api/extract/")
async def extract_emails_endpoint(
    file: UploadFile = File(...),
    user_email: str = Depends(get_current_user) 
):
    print(f"\n--- User {user_email} started an ASYNC extraction task ---")
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file format.")

    try:
        # Read file asynchronously
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        if 'Email' not in df.columns:
            df['Email'] = ""
        if 'Status' not in df.columns:
            df['Status'] = ""

        domain_col_name = 'Domains' if 'Domains' in df.columns else df.columns[1]

        print(f"Starting async extraction process for {len(df)} domains...")
        
        # 1. Boot up the Async Playwright engine
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            # Create ONE shared browser context (like an incognito window) for all tabs
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Allow maximum 10 concurrent tabs open at once
            semaphore = asyncio.Semaphore(10) 
            
            # 2. Build the task list
            tasks = []
            for index, row in df.iterrows():
                domain = str(row[domain_col_name])
                # We don't 'await' here yet. We are just adding them to a queue.
                tasks.append(check_pages_and_extract_async(domain, context, semaphore))
            
            # 3. EXECUTING THE BATCH: Run all tasks concurrently!
            # gather() smartly keeps everything in the exact original Excel row order
            results_email = await asyncio.gather(*tasks)
            
            # Clean up the browser
            await context.close()
            await browser.close()

        # 4. Process the Status Column based on the results
        results_status = []
        for i, email in enumerate(results_email):
            domain = str(df.iloc[i][domain_col_name])
            if pd.isna(domain) or domain.strip() == "" or domain.lower() == "nan":
                results_status.append("")
            elif email:
                results_status.append("Found")
            else:
                results_status.append("Not Found")

        df['Email'] = results_email
        df['Status'] = results_status

        output_stream = io.BytesIO()
        df.to_excel(output_stream, index=False, engine='openpyxl')
        output_stream.seek(0)

        headers = {
            'Content-Disposition': 'attachment; filename="extracted_emails_fast.xlsx"',
            'Access-Control-Expose-Headers': 'Content-Disposition' 
        }
        return StreamingResponse(
            output_stream, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            headers=headers
        )

    except Exception as e:
        print(f"Server error: {e}")
        raise HTTPException(status_code=500, detail=str(e))