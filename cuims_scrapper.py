from playwright.async_api import async_playwright
import json
from typing import Dict
import database as db
from datetime import datetime
from PIL import Image
from io import BytesIO
import time
import utils as utils


class CUIMSScraper:
    def __init__(self):
        self.login_url = f"https://students.cuchd.in/Login.aspx"
        db.init_db()
        
    async def scrape_user_data(self, uid,password, data_to_be_fetched) -> Dict:
        db.update_last_updated(uid, "Refreshing Data")
        
        async with async_playwright() as p:
            logged_in = False
            browser = await p.chromium.launch(headless=True)
            context = None
            page = None

            saved_state = db.load_session(uid)
            if saved_state:
                context = await browser.new_context(storage_state=saved_state)
                page = await context.new_page()
                await page.goto("https://students.cuchd.in/StudentHome.aspx")
                await page.wait_for_load_state("load")
                if page.url == "https://students.cuchd.in/StudentHome.aspx":
                    logged_in = True
            
            if not logged_in:
                context = await browser.new_context()
                page = await context.new_page()

            try:
                while not logged_in:
                    await page.goto("https://students.cuchd.in/StudentHome.aspx")
                    captcha_img = await self._login_first(page, uid, password)
                    if captcha_img:
                        captcha_txt = await utils.extract_captcha_from_img(captcha_img)
                        success = await self._login_second(page, uid, password, captcha_txt)
                        if success:
                            storage_state = await context.storage_state()
                            db.save_session(uid, storage_state)
                            logged_in = True
                        else:
                            print("Login failed. Retrying...")
                            continue
                    else:
                        print("Captcha image not found. Retrying...")
                        continue

                if data_to_be_fetched == "initial":
                
                    courses_data = await self._scrape_courses(page)
                    print("Courses data scraped successfully.")
                        
                    timetable_data =await self._scrape_timetable(page)
                    print("Timetable data scraped successfully.")
                        
                    attendance_data = await self._scrape_attendance(page)
                    print("Attendance data scraped successfully.")
                    
                    return {
                        "status": "success",
                        "data": {
                            "uid": uid,
                            "attendance": attendance_data,
                            "timetable": timetable_data,
                            "courses": courses_data
                        },
                        "scraped_at": datetime.now().isoformat()
                    }
                    
                elif data_to_be_fetched == 'marks':
                    marks_data = await self._scrape_marks(page)
                    print("Marks data scraped successfully.")
                    return {
                        "status": "success",
                        "data": {
                            "uid": uid,
                            "marks": marks_data
                        },
                        "scraped_at": datetime.now().isoformat()
                    }
                    
                    
                elif data_to_be_fetched == 'result':
                    result_data = await self._scrape_result(page)
                    print("Result data scraped successfully.")
                    return {
                        "status": "success",
                        "data": {
                            "uid": uid,
                            "result": result_data
                        },
                        "scraped_at": datetime.now().isoformat()
                    }
                    
                elif data_to_be_fetched == 'leaves':
                    leaves_data = await self._scrape_leaves(page)
                    print("Leaves data scraped successfully.")
                    return {
                        "status": "success",
                        "data": {
                            "uid": uid,
                            "leaves": leaves_data
                        },
                        "scraped_at": datetime.now().isoformat()
                    }
                    
                elif data_to_be_fetched == 'profile':                
                    profile_data = await self._scrape_profile(page)
                    print("Profile data scraped successfully.")
                    return {
                        "status": "success",
                        "data": {
                            "uid": uid,
                            "profile": profile_data
                        },
                        "scraped_at": datetime.now().isoformat()
                    }
                    
                elif data_to_be_fetched == 'datesheet':
                    datesheet_data = await self._scrape_datesheet(page)
                    print("Datesheet data scraped successfully.")
                    return {
                        "status": "success",
                        "data": {
                            "uid": uid,
                            "datesheet": datesheet_data
                        },
                        "scraped_at": datetime.now().isoformat()
                    }
                    
                elif data_to_be_fetched == 'fees':
                    fees_data = await self._scrape_fees(page)
                    print("Fees data scraped successfully.")
                    return {
                        "status": "success",
                        "data": {
                            "uid": uid,
                            "fees": fees_data
                        },
                        "scraped_at": datetime.now().isoformat()
                    }
                elif data_to_be_fetched == 'all':
                    attendance_data = await self._scrape_attendance(page)
                    print("Attendance data scraped successfully.")
                    courses_data = await self._scrape_courses(page)
                    print("Courses data scraped successfully.")
                    timetable_data = await self._scrape_timetable(page)
                    print("Timetable data scraped successfully.")
                    marks_data = await self._scrape_marks(page)
                    print("Marks data scraped successfully.")
                    profile_data = await self._scrape_profile(page)
                    print("Profile data scraped successfully.")
                    result_data = await self._scrape_result(page)
                    print("Result data scraped successfully.")
                    leaves_data = await self._scrape_leaves(page)
                    print("Leaves data scraped successfully.")
                    datesheet_data = await self._scrape_datesheet(page)
                    print("Datesheet data scraped successfully.")
                    fees_data = await self._scrape_fees(page)
                    print("Fees data scraped successfully.")
                    return {
                        "status": "success",
                        "data": {
                            "uid": uid,
                            "attendance": attendance_data,
                            "courses": courses_data,
                            "timetable": timetable_data,
                            "marks": marks_data,
                            "profile": profile_data,
                            "result": result_data,
                            "leaves": leaves_data,
                            "datesheet": datesheet_data,
                            "fees": fees_data
                        },
                        "scraped_at": datetime.now().isoformat()
                    }
                
                
            except Exception as e:
                print(f"Error during data refresh: {e}")
                return {
                    "status": "error",
                    "message": str(e),
                    "scraped_at": datetime.now().isoformat()
                }
            finally:
                db.update_last_updated(uid, datetime.now().isoformat())
                await browser.close()
    
    async def _login_first(self, page, uid, password):

        print("Filling user ID...")
        await page.fill("#txtUserId", uid)
        print("User ID filled successfully.")

        print("Clicking next button...")
        await page.click("#btnNext")
        print("Next button clicked successfully.")

        try:
            print("Waiting for captcha image...")
            await page.wait_for_selector("#imgCaptcha", timeout=10000)
            captcha_element = await page.query_selector("#imgCaptcha")
            print("Captcha image loaded successfully.")

            print("Taking screenshot of captcha...")
            captcha_bytes = await captcha_element.screenshot()
            image = Image.open(BytesIO(captcha_bytes))
            print("Captcha screenshot taken successfully.")
            return image

        except Exception as e:
            print(f"Error during captcha loading or screenshot: {e}")
            return False
        
    async def _login_second(self, page,uid: str ,password: str, captcha: str) -> bool:
        try:
            print("Filling password field...")
            await page.fill("#txtLoginPassword", password)
            print("Password field filled successfully.")

            print("Filling captcha field...")
            await page.fill("#txtcaptcha", captcha)
            print("Captcha field filled successfully.")

            print("Clicking login button...")
            await page.click("#btnLogin")
            print("Login button clicked successfully.")

            current_url = page.url
            print(f"Current URL after login attempt: {current_url}")

            if current_url == 'https://students.cuchd.in/StudentHome.aspx':
                print("Login successful.")
                return True
            else:
                print("Login failed. Retrying...")
                time.sleep(10)
                return False
            
        except Exception as e:
            return False
    
    async def _scrape_attendance(self, page) -> list:

        await page.goto('https://students.cuchd.in/frmStudentCourseWiseAttendanceSummary.aspx?type=etgkYfqBdH1fSfc255iYGw==')

        await page.wait_for_timeout(2000)  # equivalent of time.sleep(2)

        try:
            # Scroll to bottom to ensure table loads
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")

            await page.wait_for_selector("#SortTable", timeout=10000)
            tbody = await page.query_selector("xpath=//*[@id='SortTable']/tbody")
            rows = await tbody.query_selector_all("tr")

            attendance_data = []

            for row in rows:
                tds = await row.query_selector_all("td")

                if len(tds) >= 11:
                    attendance_dict = {
                        'Course Code': (await tds[0].text_content()).strip(),
                        'Title': (await tds[1].text_content()).strip(),
                        'Eligible Delivered': (await tds[8].text_content()).strip(),
                        'Eligible Attended': (await tds[9].text_content()).strip(),
                        'Eligible Percentage': (await tds[10].text_content()).strip()
                    }
                    attendance_data.append(attendance_dict)

            print("Attendance data scraped from webpage.")
            return attendance_data

        except Exception as e:
            print(f"Error scraping attendance data: {e}")
            return False
  
    async def _scrape_timetable(self, page) -> list:

        final_time_table = []

        try:
            timetable = {
                0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []
            }

            # Wait for the timetable table body
            await page.wait_for_selector("xpath=//*[@id='ContentPlaceHolder1_grdMain']/tbody", timeout=10000)
            tbody = await page.query_selector("xpath=//*[@id='ContentPlaceHolder1_grdMain']/tbody")
            rows = await tbody.query_selector_all("tr")

            for row_index, row in enumerate(rows[1:]):  # skip header
                cols = await row.query_selector_all("td")
                for col_index, val in enumerate(cols[1:]):  # skip time column
                    cell_text = (await val.text_content()).strip()

                    if cell_text:
                        period_time = (await cols[0].text_content()).strip()
                        course_data_with_time = f"{cell_text} on {period_time}"
                        timetable[col_index].append(course_data_with_time)

            for day, val in timetable.items():
                day_data = []
                for period in val:
                    period_data = {}
                    try:
                        period_parts = period.split('::')
                        subject = period_parts[0].split(':')[0]

                        teacher_data = period_parts[1].split("By ")[1].split(" at ")
                        if len(teacher_data) > 1:
                            teacher = teacher_data[0]
                            class_loc = teacher_data[1].split("on")
                        else:
                            teacher = ""
                            class_loc = teacher_data[0].split("at ")[1].split(" on ")

                        period_data['subject_code'] = subject
                        period_data['teacher'] = teacher
                        period_data['location'] = class_loc[0]
                        period_data['time'] = class_loc[1]
                        period_data['day_number'] = day + 1

                        day_data.append(period_data)
                    except Exception as e:
                        continue

                final_time_table.append(day_data)

            print("Timetable data scraped from webpage.")
            return final_time_table

        except Exception as e:
            print(f"Error scraping timetable data: {e}")
            return False

    async def _scrape_courses(self, page) -> list:

        await page.goto('https://students.cuchd.in/frmMyTimeTable.aspx')

        # Scroll to bottom to make sure table loads
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")

        try:
            # Wait for the table body
            await page.wait_for_selector("xpath=/html/body/form/div[4]/div[3]/div/div[4]/div/table/tbody", timeout=10000)
            tbody = await page.query_selector("xpath=/html/body/form/div[4]/div[3]/div/div[4]/div/table/tbody")

            rows = await tbody.query_selector_all("tr")
            courses = []

            for row in rows[1:]:  # skip header row
                cols = await row.query_selector_all("td")
                course_code = (await cols[0].text_content()).strip()
                course_name = (await cols[1].text_content()).strip()
                courses.append({
                    "course_code": course_code,
                    "course_name": course_name
                })

            print("Courses data scraped from webpage.")
            return courses

        except Exception as e:
            print(f"Error scraping courses data: {e}")
            return False

    async def _scrape_profile(self, page):

        await page.goto('https://students.cuchd.in/frmStudentProfile.aspx')

        personal_info = {}

        try:
            # Wait for personal info to load
            await page.wait_for_selector('.stuProfileData .row')

            personal_rows = await page.query_selector_all('.stuProfileData .row .col-md-5.col-xs-6 .row')

            for row in personal_rows:
                key_el = await row.query_selector('.col-sm-4')
                val_el = await row.query_selector('.col-sm-8')
                if key_el and val_el:
                    key = (await key_el.inner_text()).strip()
                    value = (await val_el.inner_text()).strip()
                    personal_info[key] = value

            # Get Education Info
            education_info = []
            try:
                await page.wait_for_selector('#ContentPlaceHolder1_gvStudentQualification tbody', timeout=3000)
                rows = await page.query_selector_all('#ContentPlaceHolder1_gvStudentQualification tbody tr')
                for row in rows[1:]:  # skip header
                    cols = await row.query_selector_all('td')
                    if len(cols) >= 5:
                        education_info.append({
                            'qualification': await cols[0].inner_text(),
                            'steram': await cols[1].inner_text(),
                            'school/college': await cols[2].inner_text(),
                            'university/board': await cols[3].inner_text(),
                            'passing_year': await cols[4].inner_text(),
                        })
            except:
                pass

            personal_info['education_info'] = education_info

            # Get Contact Info
            contact_info = []
            try:
                await page.wait_for_selector('#ContentPlaceHolder1_gvStudentContacts tbody', timeout=3000)
                rows = await page.query_selector_all('#ContentPlaceHolder1_gvStudentContacts tbody tr')
                for row in rows[1:]:
                    cols = await row.query_selector_all('td')
                    if len(cols) >= 5:
                        contact_info.append({
                            'contact_type': await cols[0].inner_text(),
                            'residence': await cols[1].inner_text(),
                            'office': await cols[2].inner_text(),
                            'mobile': await cols[3].inner_text(),
                            'email_id': await cols[4].inner_text(),
                        })
            except:
                pass

            personal_info['contact_info'] = contact_info

            print("Profile data scraped from webpage.")
            return personal_info

        except Exception as e:
            print(f"Error scraping profile data: {e}")
            return False

    async def _scrape_marks(self, page):
        
        try:

            await page.goto('https://students.cuchd.in/frmStudentMarksView.aspx')

            subjects = {}

            headers = await page.query_selector_all(".ui-accordion-header")

            for i, header in enumerate(headers):
                subject_text = (await header.inner_text()).strip()
                subjects[subject_text] = {"experiments": []}

                if i != 0:
                    await header.click()
                    await page.wait_for_timeout(1000)  # 1 sec wait after clicking

                panel_id = await header.get_attribute("aria-controls")
                panel = await page.query_selector(f"#{panel_id}")

                rows = await panel.query_selector_all("tbody tr")

                for row in rows:
                    cols = await row.query_selector_all("td")
                    if len(cols) == 3:
                        subjects[subject_text]["experiments"].append({
                            "name": (await cols[0].inner_text()).strip(),
                            "max_marks": (await cols[1].inner_text()).strip(),
                            "marks_obtained": (await cols[2].inner_text()).strip()
                        })

            print("Marks data scraped from webpage.")
            return subjects
        except:
            print("Error scraping marks data.")
            return {}
   
    async def _scrape_fees(self, page):
        await page.goto("https://students.cuchd.in/frmAccountStudentDetails.aspx")
        
        try:
            # Click the 2nd tab (Payment History)
            tab = await page.wait_for_selector(
                '#ctl00_ContentPlaceHolder1_RadTabStrip1 > div > ul > li:nth-child(2) > a > span > span > span',
                timeout=5000
            )
            await tab.click()
            await page.wait_for_timeout(1500)

            payments = []
            
            # Select all transaction blocks (each wrapped in a div)
            transaction_divs = await page.query_selector_all("div[style*='border-bottom: 1px solid']")

            for trans_div in transaction_divs:
                trans_detail = {}

                # Date
                date_div = await trans_div.query_selector(".transactions-date")
                month_div = await trans_div.query_selector(".transactions-month")
                if date_div and month_div:
                    trans_detail["payment_date"] = f"{await date_div.inner_text()} {await month_div.inner_text()}"

                # Get all <span> values inside the details table
                table = await trans_div.query_selector("table")
                tds = await table.query_selector_all("td")

                if len(tds) >= 4:
                    # 2nd TD = REF NOs and mode
                    spans = await tds[1].query_selector_all("span")
                    if len(spans) >= 6:
                        trans_detail["trans_ref_no"] = await spans[1].inner_text()
                        trans_detail["bank_ref_no"] = await spans[3].inner_text()
                        trans_detail["payment_mode"] = await spans[5].inner_text()

                    # 3rd TD = Amounts
                    amounts = await tds[2].query_selector_all("div")
                    if len(amounts) >= 3:
                        trans_detail["total_amt"] = (await amounts[0].inner_text()).split("Rs")[-1].strip()
                        trans_detail["service_tax"] = (await amounts[1].inner_text()).split("Rs")[-1].strip()
                        trans_detail["processing_fee"] = (await amounts[2].inner_text()).split("Rs")[-1].strip()

                    # 4th TD = status
                    trans_detail["status"] = (await tds[3].inner_text()).strip()

                    payments.append(trans_detail)

            print("Fees data scraped from webpage.")
            return payments

        except Exception as e:
            print(f"Error scraping fees data: {e}")
            return False
  
    async def _scrape_result(self, page):

        try:
            await page.goto("https://students.cuchd.in/result.aspx")
            await page.wait_for_timeout(2000)

            result = {}

            # DEBUG: Dump HTML to check selectors if needed
            html = await page.content()
            

            try:
                # Try to get CGPA using a safer selector
                cgpa_elem = await page.query_selector("div[id$='divCGPA'] span")
                if cgpa_elem:
                    result['cgpa'] = await cgpa_elem.inner_text()
                else:
                    result['cgpa'] = "N/A"

                result['semester_wise_result'] = []

                sem_tables = await page.query_selector_all("table[id$='dlResult'] > tbody > tr")
                for i in range(len(sem_tables)):
                    semester_res = {}

                    sem_title = await page.query_selector(f"#ContentPlaceHolder1_wucResult1_dlResult_lblSem_{i}")
                    semester_res['semester'] = await sem_title.inner_text() if sem_title else f"Semester {i+1}"

                    sgpa_text = await page.query_selector(
                        f"#ContentPlaceHolder1_wucResult1_dlResult_div_sticky_{i} > span:nth-child(3)"
                    )
                    semester_res['sgpa'] = (await sgpa_text.inner_text()).split(":")[1].strip() if sgpa_text else "N/A"

                    semester_res['semester_result'] = []

                    subject_rows = await page.query_selector_all(
                        f"#ContentPlaceHolder1_wucResult1_dlResult_Repeater1_{i} > tbody > tr"
                    )

                    for row in subject_rows[1:]:  # Skip header
                        cols = await row.query_selector_all("td")
                        if len(cols) >= 4:
                            sem_res_value = {
                                'subject_code': await cols[0].inner_text(),
                                'subject_name': await cols[1].inner_text(),
                                'subject_credits': await cols[2].inner_text(),
                                'subject_grade_ob': await cols[3].inner_text()
                            }
                            semester_res['semester_result'].append(sem_res_value)

                    result['semester_wise_result'].append(semester_res)

            except Exception as e:
                result['semester_wise_result'] = []

            print("Result data scraped from webpage.")
            return result

        except Exception as e:
            print(f"Error scraping result data: {e}")
            return False
      
    async def _scrape_datesheet(self, page):

        try:
            await page.goto('https://students.cuchd.in/frmStudentDatesheet.aspx')
            await page.wait_for_timeout(2000)

            datesheet = []

            try:
                rows = await page.query_selector_all('table tbody tr')

                for row in rows[1:]:  # Skip table header
                    cells = await row.query_selector_all('td')
                    if len(cells) < 10:
                        continue  # Just in case

                    row_data = {
                        'exam_type': await cells[0].inner_text(),
                        'datesheet_type': await cells[1].inner_text(),
                        'course_code': await cells[2].inner_text(),
                        'course_name': await cells[3].inner_text(),
                        'slot_no': await cells[4].inner_text(),
                        'exam_date': await cells[7].inner_text(),
                        'exam_time': await cells[8].inner_text(),
                    }

                    # Check for anchor tag in exam venue
                    venue_links = await cells[9].query_selector_all("a")
                    if venue_links:
                        row_data['exam_venue'] = await venue_links[0].get_attribute('href')
                    else:
                        row_data['exam_venue'] = await cells[9].inner_text()

                    datesheet.append(row_data)

            except Exception as e:
                print(f"Error parsing datesheet rows: {e}")
                return datesheet

            print("Datesheet data scraped from webpage.")
            return datesheet

        except Exception as e:
            print(f"Error scraping datesheet data: {e}")
            return False
        
    async def _scrape_leaves(self, page):
        leaves = []

        # --- DUTY LEAVE ---
        try:
            await page.goto('https://students.cuchd.in/frmStudentApplyDutyLeave.aspx')
            await page.wait_for_timeout(2000)

            tab = await page.query_selector('#__tab_Tab3')
            if tab:
                await tab.click()
                await page.wait_for_timeout(1500)

            dl_rows = await page.query_selector_all('table tbody tr')
            dl = []

            for row in dl_rows[1:]:  # Skip header
                cells = await row.query_selector_all('td')
                if len(cells) < 8:
                    continue

                dl_info = {
                    'dl_number': await cells[1].inner_text(),
                    'dl_timing': await cells[2].inner_text(),
                    'dl_category': await cells[3].inner_text(),
                    'dl_type': await cells[5].inner_text(),
                    'dl_date': await cells[6].inner_text(),
                    'dl_status': await cells[7].inner_text()
                }

                dl.append(dl_info)
            leaves.append(dl)
            print("Duty leave data scraped successfully.")
        except Exception as e:
            leaves.append([])
            print(f"Error scraping duty leave data: {e}")

        # --- MEDICAL LEAVE ---
        try:
            await page.goto('https://students.cuchd.in/frmStudentMedicalLeaveApply.aspx')
            await page.wait_for_timeout(2000)

            tab = await page.query_selector('#__tab_Tab3')
            if tab:
                await tab.click()
                await page.wait_for_timeout(1500)

            ml_rows = await page.query_selector_all('table tbody tr')
            ml = []

            for row in ml_rows[1:]:
                cells = await row.query_selector_all('td')
                if len(cells) < 8:
                    continue

                ml_info = {
                    'dl_number': await cells[1].inner_text(),
                    'dl_timing': await cells[2].inner_text(),
                    'dl_category': await cells[3].inner_text(),
                    'dl_type': await cells[5].inner_text(),
                    'dl_date': await cells[6].inner_text(),
                    'dl_status': await cells[7].inner_text()
                }

                ml.append(ml_info)
            leaves.append(ml)
            print("Medical leave data scraped successfully.")
        except Exception as e:
            leaves.append([])
            print(f"Error scraping medical leave data: {e}")

        return leaves
    
              
async def refresh_user_data(uid: str, password: str, data_to_be_fetched: str) -> Dict:
        scraper = CUIMSScraper()

        scraped_data = await scraper.scrape_user_data(uid,password, data_to_be_fetched)
        
        if scraped_data["status"] == "success":
            data = scraped_data["data"]
            
            # Initial data fetch updates multiple aspects
            if data_to_be_fetched == "initial":
                print('data-fetch-initial')
                if data.get('attendance'):
                    attendace_goal = db.get_attendance_goal(data['uid'])
                    attendance_transformed = utils.transform_attendance(data['attendance'], attendace_goal)
                    db.update_attendance(data['uid'], attendance_transformed)
                if data.get('courses'):
                    db.update_courses(data['uid'], data['courses'])
                if data.get('timetable'):
                    db.update_timetable(data['uid'], data['timetable'])
            
            elif data_to_be_fetched == 'marks' and data.get('marks'):
                db.update_marks(data['uid'], data['marks'])
            elif data_to_be_fetched == 'profile' and data.get('profile'):
                db.update_profile(data['uid'], data['profile'])
            elif data_to_be_fetched == 'result' and data.get('result'):
                db.update_result(data['uid'], data['result'])
            elif data_to_be_fetched == 'leaves' and data.get('leaves'):
                db.update_leaves(data['uid'], data['leaves'])
            elif data_to_be_fetched == 'datesheet' and data.get('datesheet'):
                db.update_datesheet(data['uid'], data['datesheet'])
            elif data_to_be_fetched == 'fees' and data.get('fees'):
                db.update_fees(data['uid'], data['fees'])
            
            elif data_to_be_fetched == 'all':
                if data.get('attendance'):
                    attendace_goal = db.get_attendance_goal(data['uid'])
                    attendance_transformed = utils.transform_attendance(data['attendance'], attendace_goal)
                    db.update_attendance(data['uid'], attendance_transformed)
                if data.get('courses'):
                    db.update_courses(data['uid'], data['courses'])
                if data.get('timetable'):
                    db.update_timetable(data['uid'], data['timetable'])
                if data.get('marks'):
                    db.update_marks(data['uid'], data['marks'])
                if data.get('profile'):
                    db.update_profile(data['uid'], data['profile'])
                if data.get('result'):
                    db.update_result(data['uid'], data['result'])
                if data.get('leaves'):
                    db.update_leaves(data['uid'], data['leaves'])
                if data.get('datesheet'):
                    db.update_datesheet(data['uid'], data['datesheet'])
                if data.get('fees'):
                    db.update_fees(data['uid'], data['fees'])

            db.update_last_updated(uid, datetime.now().isoformat())

            return {
                "status": "success",
                "message": f"{data_to_be_fetched} data refreshed successfully",
                "updated_at": datetime.now().isoformat()
            }
        else:
            return scraped_data

