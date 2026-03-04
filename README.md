# B2B Email Extraction & Verification Tool
---------------------------------------------------------
Project Version: 1.0.0
Author: Bablu Prajapati
Deployment: Hugging Face (Backend) + Vercel (Frontend)

## 1. PROJECT OVERVIEW
This professional B2B tool allows marketing teams to upload lists of business 
domains to automatically find and verify contact email addresses. The system 
uses a headless browser (Playwright) to mimic human navigation and extract 
emails from "About" and "Contact" pages, followed by a verification check 
via the Hunter.io API.

## 2. TECHNICAL ARCHITECTURE

### Frontend (React.js)
- Framework: Vite-based React
- Features: Responsive UI, State Management, Secure File Upload
- Auth: Cookie-based authentication (HttpOnly) to prevent XSS attacks.

### Backend (FastAPI)
- Framework: FastAPI (Python)
- Web Scraping: Playwright (Chromium)
- RAM Optimization: Deployed with 16GB RAM to handle headless browser load.
- Security: JWT-based session management and Bcrypt password hashing.

### Database (MongoDB)
- Database: MongoDB Atlas (Cloud)
- Collections: "users" (for auth) and "extractions" (for logs).

## 3. CORE CODE LOGIC

### Email Extraction Engine
The backend utilizes a regex-based pattern matching system combined with 
Playwright's `page.content()` to scan the full HTML of a website. It 
intelligently navigates to:
- /contact
- /contact-us
- /about
- /about-us

### Email Verification
Once emails are scraped, the backend sends the primary contact to the 
Hunter.io API to verify the deliverability status (e.g., "Valid", 
"Accept All", or "Invalid").

## 4. DEPLOYMENT STEPS

### Step 1: MongoDB Configuration
1. Create a MongoDB Atlas cluster.
2. IMPORTANT: In "Network Access", add IP address 0.0.0.0/0. This allows 
   the Hugging Face cloud server to connect to your database.

### Step 2: Hugging Face Backend Deployment
1. Create a new "Docker Space" on Hugging Face.
2. Name the configuration file exactly 'Dockerfile'.
3. Contents of Dockerfile:
   - Use official Playwright Python image.
   - Install dependencies from requirements.txt.
   - Run 'playwright install chromium'.
   - Expose port 7860 for FastAPI.
4. Add Secrets in Space Settings:
   - MONGO_URI
   - SECRET_KEY
   - HUNTER_API_KEY

### Step 3: Frontend Deployment (Vercel)
1. Push your React code to GitHub.
2. Connect GitHub to Vercel.
3. Set the Environment Variable:
   VITE_API_URL=https://your-username-your-space.hf.space
4. Add your Vercel URL to the 'origins' list in your backend 'main.py' 
   to fix CORS issues.

## 5. REPOSITORY STRUCTURE
/backend
  ├── main.py            # API Routes and Scraper Logic
  ├── requirements.txt   # Python Dependencies
  └── Dockerfile         # Deployment Configuration
/frontend
  ├── src/               # React Components (Login, Extractor)
  ├── App.jsx            # Routing and Global State
  └── .env               # API URL Configuration

## 6. USAGE INSTRUCTIONS
1. Register a new account via the Signup tab.
2. Login to receive a secure session cookie.
3. Navigate to the Extractor page.
4. Upload an Excel (.xlsx) file with a "Domains" column.
5. Wait for the extraction to finish and download the result file.
