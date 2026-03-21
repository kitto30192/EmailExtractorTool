import os
import asyncio
import re
import pandas as pd
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright
from app.database import jobs_collection
from datetime import datetime

# --- SMART FILTERS ---
JUNK_DOMAINS = ['sentry', 'wixpress', 'example.com', 'domain.com', 'yoursite.com', 'test.com', 'wix.com', 'name.com']
JUNK_PREFIXES = ['no-reply', 'noreply', 'mailer-daemon', 'donotreply', 'admin@example']

def is_clean_email(email: str) -> bool:
    email = email.lower().strip()
    if email.endswith(('.png', '.jpg', '.jpeg', '.gif', '.css', '.js', '.svg', '.webp', '.woff', '.ttf')): return False
    if any(bad in email for bad in JUNK_DOMAINS): return False
    if any(email.startswith(bad) for bad in JUNK_PREFIXES): return False
    if len(email.split('@')[0]) > 35: return False
    return True

# --- DIAGNOSTIC SCRAPER ENGINE ---
# Notice the return type is now a tuple: (emails_string, status_reason)
async def check_pages_and_extract_async(domain: str, browser, semaphore) -> tuple[str, str]:
    if pd.isna(domain) or domain.strip() == "" or domain.lower() == "nan":
        return "", "Invalid Domain"

    if not domain.startswith("http"):
        domain = "https://" + domain

    paths_to_check = ["/contact", "/contact-us", "", "/about", "/about-us"]
    extracted_emails = set()
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    # Default assumption: The site loads, but we just don't find an email.
    best_reason = "No email text found (Contact form only?)" 

    async with semaphore:
        context = await browser.new_context()
        try:
            page = await context.new_page()
            await page.route("**/*", lambda route: route.abort()
                 if route.request.resource_type in ["image", "stylesheet", "media", "font", "other"]
                 else route.continue_()
            )

            for path in paths_to_check:
                target_url = urljoin(domain, path)
                
                try:
                    response = await page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
                    
                    # --- DIAGNOSTIC CHECK 1: HTTP Status Codes ---
                    if response:
                        if response.status in [403, 401]:
                            best_reason = f"Blocked by Website ({response.status})"
                            continue # Move to next path, but unlikely to work if homepage blocked
                        elif response.status >= 500:
                            best_reason = f"Server Down ({response.status})"
                            continue
                        elif response.status == 404:
                            best_reason = f"Path {path} Not Found (404)"
                            continue

                    if "contact" in path:
                        await page.wait_for_timeout(2000) 
                    
                    # Try mailto links
                    try:
                        mailto_links = await page.evaluate("""() => {
                            return Array.from(document.querySelectorAll('a[href^="mailto:"]'))
                                .map(a => a.href.replace('mailto:', '').split('?')[0].trim());
                        }""")
                        for email in mailto_links:
                            if is_clean_email(email): extracted_emails.add(email)
                    except Exception:
                        pass 

                    # Try Regex
                    page_html = await page.content()
                    matches = re.findall(email_pattern, page_html)
                    for m in matches:
                        if is_clean_email(m): extracted_emails.add(m)

                    if extracted_emails:
                        best_reason = "Found" # Success overrides all errors
                        break

                except Exception as e:
                    # --- DIAGNOSTIC CHECK 2: Connection Errors ---
                    error_str = str(e).lower()
                    if "timeout" in error_str:
                        best_reason = "Connection Timeout"
                    elif "name not resolved" in error_str or "dns" in error_str:
                        best_reason = "Domain does not exist (DNS)"
                    elif "ssl" in error_str:
                        best_reason = "SSL Certificate Error"
                    else:
                        best_reason = "Failed to load page"
                    continue
                    
        finally:
            await context.close()

    return ", ".join(list(extracted_emails)), best_reason

async def process_excel_job_background(task_id: str, input_filepath: str, output_filepath: str):
    """Background task to process multiple sheets and update DB progress."""
    
    try:
        excel_file = pd.ExcelFile(input_filepath)
        sheet_names = excel_file.sheet_names
        excel_file.close()
        
        # Prepare an Excel writer for the final output
        writer = pd.ExcelWriter(output_filepath, engine='openpyxl')
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            semaphore = asyncio.Semaphore(10)
            
            for index, sheet in enumerate(sheet_names, start=1):
                # Update DB: Working on current sheet
                time_now = datetime.now().strftime('%I:%M:%S %p').lower()
                jobs_collection.update_one(
                    {"task_id": task_id},
                    {"$push": {"logs": f"[{time_now}] Working on Sheet {index} ('{sheet}')..."}}
                )
                
                df = pd.read_excel(input_filepath, sheet_name=sheet)
                
                # --- VALIDATION 1: Exact Columns Check ---
                expected_columns = ['SRL', 'Domains', 'Email', 'Status']
                if list(df.columns) != expected_columns:
                    time_now = datetime.now().strftime('%I:%M:%S %p').lower()
                    error_msg = f"[{time_now}] Sheet {index} ('{sheet}') skipped: Incorrect format. Expected exactly ['SLR', 'Domains', 'Email', 'Status']."
                    jobs_collection.update_one({"task_id": task_id}, {"$push": {"logs": error_msg}})
                    df.to_excel(writer, sheet_name=sheet, index=False)
                    continue

                # --- VALIDATION 2: Row Limit Check ---
                if len(df) > 500:
                    error_msg = f"Sheet {index} ('{sheet}') skipped: Exceeds 500 domains limit (found {len(df)})."
                    jobs_collection.update_one({"task_id": task_id}, {"$push": {"logs": error_msg}})
                    df.to_excel(writer, sheet_name=sheet, index=False) # Save original unedited
                    continue

                df['Domains'] = df['Domains'].fillna("").astype(str)
                df['Email'] = df['Email'].fillna("").astype(str)
                df['Status'] = df['Status'].fillna("").astype(str)

                # --- EXTRACTION PROCESS ---
                tasks = []
                for _, row in df.iterrows():
                    domain = str(row['Domains'])
                    tasks.append(check_pages_and_extract_async(domain, browser, semaphore))

                # Run batch
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results safely
                for i, res in enumerate(results):
                    domain = str(df.iloc[i]['Domains'])
                    if pd.isna(domain) or domain.strip() == "" or domain.lower() == "nan":
                        continue
                        
                    if isinstance(res, Exception):
                        df.at[i, 'Status'] = f"System Error: {str(res)[:30]}"
                    else:
                        # res is now a tuple: (emails, reason)
                        extracted_emails, status_reason = res
                        
                        df.at[i, 'Email'] = extracted_emails
                        df.at[i, 'Status'] = status_reason # Write the specific reason to the Excel sheet!

                # Save the processed sheet to the new Excel file
                df.to_excel(writer, sheet_name=sheet, index=False)
                
                # Update DB: Sheet complete
                time_now = datetime.now().strftime('%I:%M:%S %p').lower()
                jobs_collection.update_one(
                    {"task_id": task_id},
                    {"$push": {"logs": f"[{time_now}] Sheet {index} ('{sheet}') completed successfully."}}
                )

            await browser.close()
            
        # Save the final multi-sheet file
        writer.close()

        # Mark Job as Complete
        jobs_collection.update_one(
            {"task_id": task_id},
            {"$set": {"status": "Completed", "logs": jobs_collection.find_one({"task_id": task_id})["logs"] + ["All processing finished!"]}}
        )

    except Exception as e:
        jobs_collection.update_one(
            {"task_id": task_id},
            {"$set": {"status": "Failed", "logs": jobs_collection.find_one({"task_id": task_id})["logs"] + [f"Critical Server Error: {str(e)}"]}}
        )
    finally:
        # Cleanup the temporary uploaded file
        if os.path.exists(input_filepath):
            os.remove(input_filepath)