import requests
import csv
import time
import concurrent.futures
from urllib.parse import urljoin
from PIL import Image
import pytesseract
import io
from bs4 import BeautifulSoup
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# --- การตั้งค่า ---
# (สำคัญ) หากติดตั้ง Tesseract ไว้ที่อื่นที่ไม่ใช่ Default Path ให้แก้ตรงนี้
# ตัวอย่าง Windows: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# ตัวอย่าง macOS/Linux: ไม่ต้องแก้ ถ้าติดตั้งตามปกติ

# ปิดการแจ้งเตือนเรื่อง SSL Certificate ที่ไม่ปลอดภัย
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# --- การตั้งค่า ---
PATHS_TO_CHECK = [
    "", # ตรวจสอบหน้าแรกด้วย
    "video", "videos", "view", "views",
    "pgslot", "slot", "body", "db", "db/TH",
    "game", "games", "casino" , 'new' , 'news'
]

GAMBLING_KEYWORDS = [
    'pgslot', 'สล็อต', 'คาสิโน', 'พนัน', 'เดิมพัน',
    'บาคาร่า', 'แทงบอล', 'เว็บตรง', 'เครดิตฟรี',
    'ฝาก-ถอน', 'slot', 'casino', 'bonanza', 'linebet' , 
    'แตกง่าย', 'แจกจริง', 'สมัครสมาชิก'
]

INPUT_FILE = "urls.txt"
OUTPUT_FILE = "scan_results_comprehensive.csv"
MAX_WORKERS = 20 # ลดลงเล็กน้อยเพราะมีงาน OCR ที่ใช้ CPU
TIMEOUT = 15
MIN_CONTENT_LENGTH = 100
MIN_IMAGE_SIZE_BYTES = 50 * 1024 # 50 KB (กรองรูปเล็กๆ ออก)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def analyze_image_for_text(image_bytes):
    """ใช้ OCR เพื่อดึงข้อความจากรูปภาพ"""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        # ใช้ภาษาไทย (tha) และอังกฤษ (eng) ในการอ่าน
        text = pytesseract.image_to_string(image, lang='tha+eng').lower()
        return text
    except Exception as e:
        # print(f"      - OCR Error: {e}")
        return ""

def analyze_url(base_url):
    clean_base_url = base_url.strip().rstrip('/')
    if not clean_base_url.startswith(('http://', 'https://')):
        return None

    print(f"\n🔎 กำลังตรวจสอบ: {clean_base_url}")

    for path in PATHS_TO_CHECK:
        full_url = f"{clean_base_url}/{path}"
        try:
            response = requests.get(
                full_url,
                headers=HEADERS,
                timeout=TIMEOUT,
                allow_redirects=True,
                verify=False
            )

            status = response.status_code
            size = len(response.content)
            final_url = response.url # URL สุดท้ายหลังจาก Redirect

            print(f"   -> {full_url} (status={status}, size={size})")

            if status == 200 and size >= MIN_CONTENT_LENGTH:
                soup = BeautifulSoup(response.text, 'html.parser')
                page_content_lower = response.text.lower()

                # 1. ตรวจสอบข้อความใน HTML Body, Title, และ Meta Description
                title_text = soup.title.string.lower() if soup.title and soup.title.string else ""
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                meta_desc_text = meta_desc['content'].lower() if meta_desc and meta_desc.get('content') else ""
                
                search_text = page_content_lower + title_text + meta_desc_text
                
                for keyword in GAMBLING_KEYWORDS:
                    if keyword in search_text:
                        print(f"  🚨 [เจอเว็บพนัน - Text] {final_url} (Keyword: {keyword})")
                        return {'url': final_url, 'type': 'Gambling (Text)', 'keyword': keyword}

                # 2. ตรวจสอบ Attribute ของรูปภาพ และทำ OCR กับรูปภาพ
                img_tags = soup.find_all('img')
                for img_tag in img_tags:
                    # ตรวจสอบ alt text
                    alt_text = img_tag.get('alt', '').lower()
                    for keyword in GAMBLING_KEYWORDS:
                        if keyword in alt_text:
                            print(f"  🚨 [เจอเว็บพนัน - Image Alt] {final_url} (Keyword: {keyword})")
                            return {'url': final_url, 'type': 'Gambling (Image Alt)', 'keyword': keyword}
                    
                    # ดาวน์โหลดรูปมาทำ OCR
                    img_src = img_tag.get('src')
                    if not img_src:
                        continue
                    
                    img_url = urljoin(final_url, img_src)
                    try:
                        img_response = requests.get(img_url, headers=HEADERS, timeout=TIMEOUT, verify=False, stream=True)
                        if img_response.status_code == 200:
                            image_bytes = img_response.content
                            if len(image_bytes) < MIN_IMAGE_SIZE_BYTES:
                                # print(f"      - ข้ามรูปเล็ก: {img_url}")
                                continue
                            
                            print(f"      - กำลังทำ OCR รูปภาพ: {img_url}")
                            ocr_text = analyze_image_for_text(image_bytes)
                            
                            for keyword in GAMBLING_KEYWORDS:
                                if keyword in ocr_text:
                                    print(f"  🚨 [เจอเว็บพนัน - OCR] {final_url} (Keyword: {keyword} บนรูปภาพ)")
                                    return {'url': final_url, 'type': 'Gambling (OCR)', 'keyword': keyword}
                    except requests.exceptions.RequestException:
                        # print(f"      - Download รูปไม่สำเร็จ: {img_url}")
                        continue
                
                # ถ้าไม่เจอ Keyword แต่มีเนื้อหา
                print(f"  ✅ [เจอหน้ามีเนื้อหา] {final_url} (Size: {size})")
                return {'url': final_url, 'type': 'Content', 'keyword': '-'}

        except requests.exceptions.RequestException as e:
            # print(f"   ✖ Error ที่ {full_url} : {e}")
            continue

    return None

def main():
    print(f"🚀 เริ่มการสแกน (เวอร์ชันครอบคลุม) จากไฟล์ '{INPUT_FILE}'...")
    start_time = time.time()

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            urls_to_scan = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ ไม่พบไฟล์ '{INPUT_FILE}'")
        return

    print(f"พบ {len(urls_to_scan)} URL ที่ต้องตรวจสอบ\n")

    found_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(analyze_url, url): url for url in urls_to_scan}

        for future in concurrent.futures.as_completed(future_to_url):
            result = future.result()
            if result:
                found_results.append(result)

    print("\n----------------------------------------")
    print(f"🎉 สแกนเสร็จสิ้น! พบ {len(found_results)} URL ที่เข้าเงื่อนไข")

    if found_results:
        found_results.sort(key=lambda x: x['type'], reverse=True)
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['url', 'type', 'keyword']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(found_results)
        print(f"💾 บันทึกผลลัพธ์ที่ '{OUTPUT_FILE}' แล้ว")

    end_time = time.time()
    print(f"⏱️ ใช้เวลาทั้งหมด: {end_time - start_time:.2f} วินาที")

if __name__ == "__main__":
    main()
