import asyncio
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta
import jwt
from typing import Optional
from config import get_config
import database as db
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from cuims_scrapper import refresh_user_data
from pydantic import BaseModel
import base64
from playwright.async_api import async_playwright

load_dotenv()
print("Starting FastAPI application...")
app = FastAPI(title="Web Automation Dashboard")
print("FastAPI application initialized.")

print("Mounting static files...")
app.mount("/static", StaticFiles(directory="static"), name="static")
print("Static files mounted successfully.")

templates = Jinja2Templates(directory="templates")
print("Initializing database...")
db.init_db()
print("Database initialized successfully.")

print("Loading configuration...")
config = get_config()
print("Configuration loaded successfully.")

print("Setting up encryption key...")
FERNET_KEY = config["FERNET_KEY"]
fernet = Fernet(FERNET_KEY.encode())
print("Encryption key set up successfully.")

def verify_token(token: str):
    print("Verifying token...")
    try:
        config = get_config()
        payload = jwt.decode(token, str(config['SECRET_KEY']), algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            print("Token verification failed: username is None.")
            return None
        print("Token verified successfully.")
        return username
    except jwt.PyJWTError:
        print("Token verification failed: PyJWTError.")
        return None

def encrypt_password(password: str) -> str:
    print("Encrypting password...")
    return fernet.encrypt(password.encode()).decode()
    print("Password encrypted successfully.")

def decrypt_password(encrypted_password: str) -> str:
    print("Decrypting password...")
    return fernet.decrypt(encrypted_password.encode()).decode()
    print("Password decrypted successfully.")

def verify_password(plain_password: str, encrypted_password: str) -> bool:
    print("Verifying password...")
    try:
        decrypted = decrypt_password(encrypted_password)
        result = decrypted == plain_password
        print(f"Password verification result: {result}")
        return result
    except Exception:
        print("Password verification failed: Exception occurred.")
        return False 

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    uid = verify_token(token)
    if not uid:
        return None
    user = db.get_user_by_uid(uid)
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    print("Creating access token...")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=30)
    to_encode.update({"exp": expire})
    config = get_config()
    encoded_jwt = jwt.encode(to_encode, str(config['SECRET_KEY']), algorithm="HS256")
    print("Access token created successfully.")
    return encoded_jwt

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    print("Handling home route...")
    user = get_current_user(request)
    if not user:
        print("User not authenticated. Redirecting to login page.")
        return RedirectResponse(url="/login", status_code=302)
    print("User authenticated. Redirecting to dashboard.")
    return RedirectResponse(url="/dashboard", status_code=302)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    print("Handling login page route...")
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, uid: str = Form(...), password: str = Form(...)):
    print("Handling login request...")
    user = db.get_user_by_uid(uid)
    if not user:
        print("User not found. Redirecting to welcome page.")
        return templates.TemplateResponse("welcome.html", {
            "request": request,
            "uid": uid,
            "password": password
        })
    if not verify_password(password, user["hashed_password"]):
        print("Invalid credentials. Redirecting to login page.")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid credentials"
        })
    access_token = create_access_token(data={"sub": user["uid"]})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=30 * 24 * 60 * 60,  # 30 days
        httponly=True,
        secure=True  # Set to True in production with HTTPS
    )
    print("Login successful. Redirecting to home page.")
    return response

@app.post("/register")
async def register(request: Request, uid: str = Form(...), password: str = Form(...)):
    print("Handling register request...")
    hashed_password = encrypt_password(password)
    user_doc = db.create_user_document(uid, hashed_password)
    access_token = create_access_token(data={"sub": uid})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=30 * 24 * 60 * 60,  # 30 days
        httponly=True,
        secure=True
    )
    print("Registration successful. Redirecting to home page.")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, success: Optional[bool] = False):
    print("Handling dashboard route...")
    user = get_current_user(request)
    if not user:
        print("User not authenticated. Redirecting to login page.")
        return RedirectResponse(url="/login", status_code=302)
    name = db.get_profile(user['uid'])['Name']
    branch = db.get_profile(user['uid'])['Program Code']
    attendance = db.get_attendance(user['uid'])
    last_updated = db.get_last_updated(user['uid'])
    last_updated = datetime.fromisoformat(last_updated) if last_updated != "Refreshing Data" else last_updated
    print("Dashboard data fetched successfully.")
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "name": name,
        "user": user,
        "branch":branch,
        "attendance": attendance,
        "active_page": 'dashboard',
        "last_updated": last_updated,
        "success": success
    })

@app.get("/predictor", response_class=HTMLResponse)
async def predictor(request : Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    last_updated = db.get_last_updated(user['uid'])
    last_updated = datetime.fromisoformat(last_updated) if last_updated != "Refreshing Data" else last_updated
    attendance = db.get_attendance(user['uid'])
    timetable = db.get_timetable(user['uid'])
    return templates.TemplateResponse("predictor.html", {
        "request": request,
        "timetable": timetable,
        "attendance": attendance,
        "active_page" : 'predictor',
        "last_updated" : last_updated
    })

@app.get("/timetable", response_class=HTMLResponse)
async def timetable(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    timetable = db.get_timetable(user['uid'])
    courses = db.get_courses(user['uid'])
    last_updated = db.get_last_updated(user['uid'])
    last_updated = datetime.fromisoformat(last_updated)if last_updated != "Refreshing Data" else last_updated
    course_map = {course["course_code"]: course["course_name"] for course in courses}
    today_date = datetime.now().strftime("%A, %B %d, %Y")
    today_weekday = datetime.today().weekday()
    timetable_today = timetable[today_weekday]
    week_dict = {
        0 : "Monday",
        1 : "Tuesday",
        2 : "Wednesday",
        3 : "Thursday",
        4 : "Friday",
        5 : "Saturday",
        6 : "Sunday"
    }
    return templates.TemplateResponse("timetable.html", {
        "request": request,
        "timetable": timetable,
        "today_date":today_date,
        "timetable_today" : timetable_today,
        "timetable_week":timetable,
        "courses" : course_map,
        "week_dict": week_dict,
        "active_page" : 'timetable',
        "last_updated" : last_updated
    })
    
@app.get("/more")
async def more(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    last_updated = db.get_last_updated(user['uid'])
    last_updated = datetime.fromisoformat(last_updated) if last_updated != "Refreshing Data" else last_updated
    return templates.TemplateResponse("more.html",{
        "request": request,
        "active_page" : "more",
        "last_updated" : last_updated
    })

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response


class RefreshRequest(BaseModel):
    data_to_be_fetched: str
    
@app.post("/refresh-data")
async def refresh_data(request: Request, data_to_be_fetched: Optional[str] = Form(None)):
    # Try to read from JSON if form param not sent
    if data_to_be_fetched is None:
        try:
            body = await request.json()
            data_to_be_fetched = body.get("data_to_be_fetched")
        except:
            raise HTTPException(status_code=400, detail="Missing data_to_be_fetched")

    if not data_to_be_fetched:
        raise HTTPException(status_code=400, detail="data_to_be_fetched is required")

    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    print('refresh-data', data_to_be_fetched)
    
    result = await refresh_user_data(user['uid'], decrypt_password(user['hashed_password']), data_to_be_fetched)

    if result["status"] == "success":
        if data_to_be_fetched == 'initial':
            return RedirectResponse(url="/dashboard?success=true", status_code=302)
        else:
            return {"status": "success"}
    else:
        raise HTTPException(status_code=500, detail=result["message"])

@app.get("/get-status")
async def get_status(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    status = db.get_last_updated(user['uid'])
    return {"status": status}


class FirstTimeUserRequest(BaseModel):
    uid: str
    password: str
    step: str = "first"
    captcha: str = None

# app.py (FastAPI)
sessions = {}  # store {uid: {page, browser, context}}

@app.post("/first-time-user")
async def first_time_user(data: FirstTimeUserRequest):
    uid = data.uid
    password = data.password

    if data.step == "first":
        p = await async_playwright().start()
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://students.cuchd.in/Login.aspx")
        await page.fill("#txtUserId", uid)
        await page.click("#btnNext")
        await page.wait_for_selector("#imgCaptcha")

        captcha_element = await page.query_selector("#imgCaptcha")
        captcha_bytes = await captcha_element.screenshot()
        image_b64 = base64.b64encode(captcha_bytes).decode()

        sessions[uid] = {
            "page": page,
            "browser": browser,
            "context": context,
        }

        return JSONResponse(content={"status": "captcha", "captcha_image": image_b64})

    elif data.step == "second":
        captcha = data.captcha
        session = sessions.get(uid)

        if not session:
            return JSONResponse(content={"status": "error", "msg": "Session expired"})

        page = session["page"]

        await page.fill("#txtLoginPassword", password)
        await page.fill("#txtcaptcha", captcha)
        await page.click("#btnLogin")
        await page.wait_for_timeout(2000)

        if page.url == 'https://students.cuchd.in/StudentHome.aspx':
            # Clean up!
            # await session["browser"].close()
            # sessions.pop(uid, None)
            return JSONResponse(content={"status": "success"})
        else:
            await session["browser"].close()
            sessions.pop(uid, None)
            return JSONResponse(content={"status": "error", "msg": "Invalid login"})
        
    elif data.step == 'third':
        session = sessions.get(uid)
        page = session["page"]
        context = session['context']
        
        storage_state = await context.storage_state()
        db.save_session(uid, storage_state)
        
        await session["browser"].close()
        sessions.pop(uid, None)
        
        add_new_data = await refresh_user_data(uid,password,'all')
        
        if add_new_data['status'] == 'success':
            return JSONResponse(content={"status": "success"})
        


@app.get("/more/marks")
async def marks(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    last_updated = db.get_last_updated(user['uid'])
    last_updated = datetime.fromisoformat(last_updated) if last_updated != "Refreshing Data" else last_updated

    marks_data = db.get_marks(user["uid"])
    labels, data = [], []

    for subject, details in marks_data.items():
        labels.append(subject.split('(')[0].strip())

        obtained = sum(
            float(exp["marks_obtained"]) if str(exp["marks_obtained"]).replace('.', '', 1).isdigit() else 0.0
            for exp in details["experiments"]
        )

        max_marks = sum(
            float(exp["max_marks"]) if str(exp["max_marks"]).replace('.', '', 1).isdigit() else 0.0
            for exp in details["experiments"]
        )

        avg_percentage = round((obtained / max_marks) * 100) if max_marks else 0
        data.append(avg_percentage)

    return templates.TemplateResponse("marks.html", {
        "request": request,
        "marks": marks_data,
        "radar_labels": labels,
        "radar_data": data,
        "active_page": "more",
        "last_updated": last_updated
    })

@app.get("/more/result")
async def result(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    last_updated = db.get_last_updated(user['uid'])
    last_updated = datetime.fromisoformat(last_updated) if last_updated != "Refreshing Data" else last_updated

    result_data = db.get_result(user["uid"])
    return templates.TemplateResponse("result.html", {
        "request": request,
        "result": result_data,
        "active_page": "more",
        "last_updated": last_updated
    })

@app.get("/more/profile")
async def profile(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    last_updated = db.get_last_updated(user['uid'])
    last_updated = datetime.fromisoformat(last_updated) if last_updated != "Refreshing Data" else last_updated

    profile_data = db.get_profile(user["uid"])
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "profile_data": profile_data,
        "active_page": "more",
        "last_updated": last_updated
    })

@app.get("/more/leaves")
async def leaves(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    last_updated = db.get_last_updated(user['uid'])
    last_updated = datetime.fromisoformat(last_updated) if last_updated != "Refreshing Data" else last_updated

    leaves_data = db.get_leaves(user["uid"])
    return templates.TemplateResponse("leaves.html", {
        "request": request,
        "leaves": leaves_data,
        "active_page": "more",
        "last_updated": last_updated
    })

@app.get("/more/fees")
async def fees(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    last_updated = db.get_last_updated(user['uid'])
    last_updated = datetime.fromisoformat(last_updated) if last_updated != "Refreshing Data" else last_updated

    fees_data = db.get_fees(user["uid"])
    return templates.TemplateResponse("fees.html", {
        "request": request,
        "fees": fees_data,
        "active_page": "more",
        "last_updated": last_updated
    })

@app.get("/more/datesheet")
async def datesheet(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    last_updated = db.get_last_updated(user['uid'])
    last_updated = datetime.fromisoformat(last_updated) if last_updated != "Refreshing Data" else last_updated

    datesheet_data = db.get_datesheet(user["uid"])
    return templates.TemplateResponse("datesheet.html", {
        "request": request,
        "datesheet_data": datesheet_data,
        "active_page": "more",
        "last_updated": last_updated
    })

@app.get("/more/settings")
async def settings(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    last_updated = db.get_last_updated(user['uid'])
    last_updated = datetime.fromisoformat(last_updated) if last_updated != "Refreshing Data" else last_updated

    goal = db.get_attendance_goal(user['uid'])
    
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "active_page": "more",
        "attendance_goal" : goal,
        "last_updated": last_updated
    })

@app.get("/more/about")
async def about(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    last_updated = db.get_last_updated(user['uid'])
    last_updated = datetime.fromisoformat(last_updated) if last_updated != "Refreshing Data" else last_updated

    return templates.TemplateResponse("about.html", {
        "request": request,
        "active_page": "more",
        "last_updated": last_updated
    })

class GoalInput(BaseModel):
    attendance_goal: int

@app.post("/apply_settings")
async def apply_settings(request: Request, data: GoalInput):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db.set_goal_value(user["uid"], data.attendance_goal)

    return JSONResponse(content={"success": True})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)


