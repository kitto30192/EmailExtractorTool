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
    response.delete_cookie("access_token")
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


def check_pages_and_extract(domain: str, browser) -> str:
    """
    Visits the domain to extract emails from the full HTML source code.
    """
    if not domain.startswith("http"):
        domain = "https://" + domain
        
    paths_to_check = ["", "/contact", "/contact-us", "/about", "/about-us"]
    extracted_emails = set()
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = context.new_page()

    for path in paths_to_check:
        target_url = urljoin(domain, path)
        print(f"  -> Checking: {target_url}")
        try:
            # Notice there are no 'await' keywords here
            page.goto(target_url, wait_until="networkidle", timeout=50000)
            page_html = page.content()
            
            matches = re.findall(email_pattern, page_html)
            
            valid_emails = [
                m for m in matches 
                if not m.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.css', '.js', '.svg'))
            ]
            
            extracted_emails.update(valid_emails)
            
        except Exception as e:
            print(f"  -> Skipped {target_url} (Error/Timeout)")
            continue

    context.close()
    return ", ".join(extracted_emails)

def verify_email_with_hunter(extracted_emails: str) -> str:
    """
    Sends the extracted email to Hunter.io to verify if it is safe to send to.
    If multiple emails were found, it verifies the first one to save API credits.
    """
    if not extracted_emails or not HUNTER_API_KEY:
        return "Not Verified"
        
    # Grab the first email from the comma-separated list
    first_email = extracted_emails.split(",")[0].strip()
    
    url = f"https://api.hunter.io/v2/email-verifier?email={first_email}&api_key={HUNTER_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Hunter returns status as: "valid", "invalid", "accept_all", or "webmail"
            status = data.get("data", {}).get("status", "unknown")
            return status.capitalize()
        else:
            return f"API Error: {response.status_code}"
    except Exception as e:
        print(f"Hunter API connection failed: {e}")
        return "Verification Failed"


@app.post("/api/extract/")
def extract_emails_endpoint(
    file: UploadFile = File(...),
    user_email: str = Depends(get_current_user) 
):
    print(f"\n--- User {user_email} started an extraction task ---")
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload an Excel file.")

    try:
        # 1. Read the uploaded Excel file synchronously
        contents = file.file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        if 'Email' not in df.columns:
            df['Email'] = ""
        if 'Status' not in df.columns:
            df['Status'] = ""

        domain_col_name = 'Domains' if 'Domains' in df.columns else df.columns[1]

        results_email = []
        results_status = []
        results_verification = [] # <-- NEW LIST FOR HUNTER STATUS

        print("Starting extraction process...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            for index, row in df.iterrows():
                domain = str(row[domain_col_name])
                
                if pd.isna(domain) or domain.strip() == "" or domain.lower() == "nan":
                    results_email.append("")
                    results_status.append("")
                    results_verification.append("") # <-- Keep rows aligned
                    continue
                    
                print(f"Scanning: {domain}")
                emails = check_pages_and_extract(domain, browser)
                
                results_email.append(emails)
                
                if emails: 
                    results_status.append("Found")
                    # --- CALL HUNTER.IO HERE ---
                    print(f"Verifying email with Hunter.io...")
                    verification = verify_email_with_hunter(emails)
                    results_verification.append(verification)
                else:
                    results_status.append("Not Found")
                    results_verification.append("N/A")
                
            browser.close()

        # Update the DataFrame with the new columns
        df['Email'] = results_email
        df['Status'] = results_status
        df['Verification Status'] = results_verification # <-- ADD NEW COLUMN TO EXCEL

        output_stream = io.BytesIO()
        df.to_excel(output_stream, index=False, engine='openpyxl')
        output_stream.seek(0)

        # 6. Return the file to the React frontend
        headers = {
            'Content-Disposition': 'attachment; filename="extracted_emails.xlsx"',
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