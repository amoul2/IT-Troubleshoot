# README — สคริปต์สแกนเว็บหา “การพนัน/คาสิโน” ด้วย Text + Image OCR

สคริปต์นี้ช่วยสแกนรายการเว็บไซต์จากไฟล์ `urls.txt` เพื่อระบุว่าหน้าเว็บมี **เนื้อหาที่เข้าข่ายเว็บพนัน/คาสิโน** หรือไม่ โดยตรวจทั้ง

1. ข้อความในหน้า (HTML/Title/Meta), 2) ข้อความใน `alt` ของรูปภาพ, และ 3) ข้อความบนรูปภาพจริงด้วย **OCR (Thai+English)**  
   ผลลัพธ์สรุปลงไฟล์ CSV ชื่อ `scan_results_comprehensive.csv`



## คุณสมบัติ

- ✅ ตรวจหลาย path ยอดฮิตอัตโนมัติ (เช่น `/video`, `/slot`, `/casino`, ฯลฯ)

- ✅ ค้นหา **คีย์เวิร์ดพนัน** ทั้งภาษาไทย/อังกฤษ ใน HTML, `<img alt>`, และ ข้อความบนภาพ

- ✅ รองรับ **ภาษาไทย + อังกฤษ** สำหรับ OCR (`lang='tha+eng'`)

- ✅ ทำงานแบบขนาน (multithread) เร็วขึ้นบนลิสต์ URL จำนวนมาก

- ✅ บันทึกผลเป็น CSV พร้อมชนิดที่พบ (`Gambling (Text)`, `Gambling (Image Alt)`, `Gambling (OCR)`, หรือ `Content`)





## โครงสร้างไฟล์

project/
├─ script.py                         # โค้ดหลัก (ตามที่ให้มา)
├─ urls.txt                          # รายการ URL เป้าหมาย (1 บรรทัดต่อ 1 URL)
└─ scan_results_comprehensive.csv    # (เอาต์พุต) สรุปผลการสแกน



## ข้อกำหนดก่อนใช้งาน (Prerequisites)

- Python 3.8+

- ติดตั้ง Tesseract OCR
  
  - **Windows:** ดาวน์โหลดตัวติดตั้งจากโครงการ Tesseract (เช่น UB Mannheim build) แล้วจด path ที่ติดตั้ง  
    ตัวอย่าง path: `C:\Program Files\Tesseract-OCR\tesseract.exe`
  
  - **macOS:** `brew install tesseract`
  
  - **Linux (Debian/Ubuntu):** `sudo apt-get install tesseract-ocr tesseract-ocr-tha`

- ภาษา OCR:
  
  - ต้องมีภาษาไทย (`tha`) และอังกฤษ (`eng`) ติดตั้งใน Tesseract  
    บน Ubuntu อาจใช้: `sudo apt-get install tesseract-ocr-tha`
    
    

Python packages:

`pip install requests beautifulsoup4 pillow pytesseract`



⚠️ หาก **Windows** และติดตั้ง Tesseract ไม่ใช่ path ปกติ ให้ตั้งค่านี้ในโค้ด:

`pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'`



## การเตรียม `urls.txt`

ใส่ URL เป้าหมายทีละบรรทัด (ต้องขึ้นต้นด้วย `http://` หรือ `https://`) เช่น

`https://example.com https://example.org http://demo.site`



## วิธีใช้งาน

รันสคริปต์:

`python script.py`

ระหว่างทำงานจะแสดงสถานะ เช่น URL ที่กำลังเช็ค, HTTP status, ขนาดเนื้อหา, และจุดที่พบคีย์เวิร์ด หากสแกนเสร็จจะสรุปจำนวนที่พบและบันทึกลง `scan_results_comprehensive.csv`

---

## ค่าตั้งค่า (ปรับได้ในไฟล์สคริปต์)

- `PATHS_TO_CHECK` : รายชื่อ path ที่จะต่อท้าย URL เพื่อตรวจ (รวมหน้าแรกด้วย `""`)

- `GAMBLING_KEYWORDS` : รายการคีย์เวิร์ดต้องสงสัย

- `INPUT_FILE` / `OUTPUT_FILE` : ชื่อไฟล์อินพุต/เอาต์พุต

- `MAX_WORKERS` : จำนวน threads พร้อมกัน (มากขึ้น = เร็วขึ้น แต่ใช้ทรัพยากรเพิ่ม)

- `TIMEOUT` : timeout ต่อคำขอ (วินาที)

- `MIN_CONTENT_LENGTH` : ขนาดขั้นต่ำของเพจที่จะถือว่า “มีเนื้อหา” (ตัวกรองเพจเปล่า)

- `MIN_IMAGE_SIZE_BYTES` : ขนาดไฟล์ภาพขั้นต่ำที่จะส่งเข้า OCR (กรองรูปเล็ก/ไอคอน)



## รูปแบบผลลัพธ์ (CSV)

ไฟล์ `scan_results_comprehensive.csv` จะมีคอลัมน์:

- `url` : URL สุดท้ายหลัง redirect ที่พบสัญญาณ

- `type` : ประเภทที่พบ
  
  - `Gambling (Text)` — พบคีย์เวิร์ดในข้อความ HTML/Title/Meta
  
  - `Gambling (Image Alt)` — พบคีย์เวิร์ดใน `alt` ของรูป
  
  - `Gambling (OCR)` — พบคีย์เวิร์ดบน **ภาพ** หลังทำ OCR
  
  - `Content` — เป็นหน้าที่มีเนื้อหาแต่ **ไม่** พบคีย์เวิร์ดพนัน

- `keyword` : คีย์เวิร์ดที่ทำให้ trigger (หรือ `-` หากเป็น `Content`)

ตัวอย่าง:

`url,type,keyword https://example.com/slot,Gambling (Text),slot https://example.com/images/banner.jpg,Gambling (OCR),สล็อต https://example.org/news,Content,-`

---

## แนวทางเพิ่มประสิทธิภาพ

- เพิ่ม/ลด `MAX_WORKERS` ตามจำนวนคอร์ CPU และแบนด์วิธ

- ปรับ `MIN_IMAGE_SIZE_BYTES` ให้สูงขึ้นเพื่อลดงาน OCR ที่ไม่จำเป็น

- ขยาย `GAMBLING_KEYWORDS` ให้ครอบคลุมคำสะกดผิด/สแลง

- เพิ่ม path เฉพาะทางลงใน `PATHS_TO_CHECK` ตามพฤติกรรมเว็บเป้าหมาย
