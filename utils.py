import requests
from PIL import Image
from io import BytesIO
from config import get_config
from dotenv import load_dotenv

async def extract_captcha_from_img(image: bytes) -> str:
        print("\n[CUIMS BACKEND EXTRACT CAPTCHA - CAPTCHA_SOLVING]\n")

        # Convert bytes to image if needed
        if isinstance(image, bytes):
            img = Image.open(BytesIO(image))
        else:
            img = image

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        load_dotenv()
        apikey = get_config()['OCR_KEY']

        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={'file': ('captcha.png', buffer, 'image/png')},
            data={
                'apikey': apikey, 
                'language': 'eng',
                'isOverlayRequired': 'false'
            }
        )
        
        def filter_text(text, whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"):
            print(f'og text: ', text)
            corrected_text = ''.join(c for c in text if c in whitelist)
            print(f'corrected Text: ', corrected_text)
            return corrected_text

        try:
            result = response.json()
            return filter_text(result['ParsedResults'][0]['ParsedText'].strip())
        
        except Exception as e:
            print("OCR failed:", e)
            return ""
        
def transform_attendance(attendance_data: list, goal=75) -> list:
    transformed = []

    for subject in attendance_data:
        code = subject['Course Code']
        name = subject['Title']
        attended = int(subject['Eligible Attended'])
        total = int(subject['Eligible Delivered'])

        missed = total - attended
        percentage = round((attended / total) * 100, 2) if total else 0.0

        # Calculate how many more classes you can miss
        can_miss = 0
        status = ""
        message = ""

        # Calculate max allowed misses to still maintain goal%
        if total > 0:
            max_miss_allowed = int((1 - goal / 100) * total)
            actual_miss = total - attended

            if percentage > goal:
                # How many more can be missed to *just* reach goal%
                x = 0
                while True:
                    new_attended = attended
                    new_total = total + x
                    new_percentage = (new_attended / new_total) * 100
                    if new_percentage < goal:
                        break
                    x += 1
                can_miss = x - 1
                status = "safe"
                message = f"✅ You can miss {can_miss} more class{'es' if can_miss != 1 else ''}"
            elif percentage == goal:
                status = "warning"
                message = "⚠️ You're exactly at the limit!"
            else:
                # How many classes to attend to reach goal%
                x = 1
                while True:
                    new_attended = attended + x
                    new_total = total + x
                    new_percentage = (new_attended / new_total) * 100
                    if new_percentage >= goal:
                        break
                    x += 1
                status = "critical"
                message = f"❌ You have to attend {x} more class{'es' if x != 1 else ''}"
        else:
            status = "critical"
            message = "❌ No classes delivered yet"

        transformed.append({
            "name": name,
            "code": code,
            "attended": attended,
            "total": total,
            "missed": missed,
            "percentage": percentage,
            "can_miss_message": message,
            "status": status
        })

    return transformed

