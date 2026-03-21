import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from app.dependencies import get_current_user
from app.database import jobs_collection
from app.services.scraper import process_excel_job_background
from datetime import datetime



router = APIRouter(prefix="/api", tags=["Extraction"])

# Ensure a temp folder exists for storing files while they process
os.makedirs("temp_files", exist_ok=True)


@router.post("/extract/")
async def start_extraction_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_email: dict = Depends(get_current_user) # Assuming this returns a dict with the user info
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file format.")

    # 1. Generate unique Task ID
    task_id = str(uuid.uuid4())
    input_filepath = f"temp_files/input_{task_id}.xlsx"
    output_filepath = f"temp_files/output_{task_id}.xlsx"

    # 2. Save the uploaded file locally so the background task can read it
    with open(input_filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. Create initial database record
    time_now = datetime.now().strftime('%I:%M:%S %p').lower()
    
    # Check if user_email is a string or a dict from your auth dependency
    # If get_current_user returns a dict like {"email": "user@test.com"}, extract it:
    email_str = user_email if isinstance(user_email, str) else user_email.get("email")

    jobs_collection.insert_one({
        "task_id": task_id,
        "user_email": email_str,         # Keeps track of whose history this belongs to
        "filename": file.filename,       # <-- NEW: Saves the file name (e.g., "leads.xlsx")
        "created_at": datetime.now(),    # <-- NEW: Saves the exact date/time object for sorting
        "status": "Processing",
        "logs": [f"[{time_now}] Upload successful. Starting extraction..."] # <-- Updated with timestamp
    })

    # 4. Trigger the background process
    background_tasks.add_task(process_excel_job_background, task_id, input_filepath, output_filepath)

    # 5. Immediately return the task_id to the frontend
    return {"message": "Extraction started", "task_id": task_id}

@router.get("/extract/status/{task_id}")
async def get_extraction_status(task_id: str, user_email: str = Depends(get_current_user)):
    job = jobs_collection.find_one({"task_id": task_id, "user_email": user_email}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return job


@router.get("/extract/download/{task_id}")
async def download_extracted_file(task_id: str, user_email: str = Depends(get_current_user)):
    job = jobs_collection.find_one({"task_id": task_id, "user_email": user_email})
    if not job or job["status"] != "Completed":
        raise HTTPException(status_code=400, detail="File is not ready yet.")

    output_filepath = f"temp_files/output_{task_id}.xlsx"
    if not os.path.exists(output_filepath):
        raise HTTPException(status_code=404, detail="File lost or deleted.")

    return FileResponse(
        path=output_filepath, 
        filename="extracted_emails_completed.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
@router.get("/history/")
async def get_user_history(user_email: dict = Depends(get_current_user)): 
    try:
        # 1. Safely get the user's email from the token
        email_str = user_email if isinstance(user_email, str) else user_email.get("email")
        
        # 2. Find their last 10 jobs in MongoDB, sorted newest to oldest
        history_cursor = jobs_collection.find(
            {"user_email": email_str}, 
            {"_id": 0, "filename": 1, "created_at": 1, "status": 1} 
        ).sort("created_at", -1).limit(10)
        
        history_list = list(history_cursor)
        
        # 3. Format the timestamps nicely for React
        for item in history_list:
            if "created_at" in item and item["created_at"]:
                item["date"] = item["created_at"].strftime("%b %d, %Y")
                item["time"] = item["created_at"].strftime("%I:%M %p")
            else:
                item["date"] = "Unknown Date"
                item["time"] = "--:--"
                
        return {"history": history_list, "user_email": email_str}
        
    except Exception as e:
        return {"error": str(e)}