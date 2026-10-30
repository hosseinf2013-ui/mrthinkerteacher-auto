import urllib.request
import xml.etree.ElementTree as ET
import re
import html
import time
from deep_translator import GoogleTranslator, MyMemoryTranslator

NASA_RSS_URL = "https://www.nasa.gov/news-release/feed/"

def translate_safe(text):
    if not text or not text.strip():
        return ""
    try:
        time.sleep(1)
        return GoogleTranslator(source='en', target='fa').translate(text)
    except Exception as e:
        print(f"Google translate limit hit: {e}. Trying fallback...")
    
    try:
        time.sleep(1)
        return MyMemoryTranslator(source='en-US', target='fa-IR').translate(text)
    except Exception as e:
        print(f"Fallback translation error: {e}")
        return text

try:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    req = urllib.request.Request(NASA_RSS_URL, headers=headers)
    response = urllib.request.urlopen(req, timeout=20)
    xml_data = response.read()

    root = ET.fromstring(xml_data)
    channel = root.find('channel')
    latest_item = channel.find('item')

    title_en = latest_item.find('title').text.strip() if latest_item.find('title') is not None else ""
    link_en = latest_item.find('link').text.strip() if latest_item.find('link') is not None else ""

    # استخراج تصویر از enclosure
    image_url = ""
    enclosure = latest_item.find('enclosure')
    if enclosure is not None and 'url' in enclosure.attrib:
        image_url = enclosure.attrib['url']

    # باز کردن صفحه اصلی خبر برای گرفتن متن کامل و مفصل مقاله
    raw_desc = ""
    if link_en:
        try:
            req_page = urllib.request.Request(link_en, headers=headers)
            page_response = urllib.request.urlopen(req_page, timeout=20)
            page_html = page_response.read().decode('utf-8', errors='ignore')
            
            # استخراج پاراگراف‌های متن اصلی از صفحه وب ناسا
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', page_html, re.DOTALL)
            extracted_text = []
            for p in paragraphs:
                clean_p = re.sub(r'<[^>]+>', '', p).strip()
                if len(clean_p) > 40:  # رد کردن پاراگراف‌های کوتاه یا منوهای سایت
                    extracted_text.append(clean_p)
            
            if extracted_text:
                raw_desc = " \n\n ".join(extracted_text[:6]) # گرفتن تا ۶ پاراگراف کامل
        except Exception as web_err:
            print(f"Could not fetch full article page, falling back to RSS desc: {web_err}")

    # اگر نتوانست صفحه وب را بخواند، از description معمولی فید استفاده کند
    if not raw_desc and latest_item.find('description') is not None:
        raw_desc = latest_item.find('description').text

    # پیدا کردن تصویر از داخل صفحه اگر در enclosure نبود
    if not image_url and 'page_html' in locals():
        img_match = re.search(r'<img[^>]+src=["\'](https://[^"\']+?\.(?:jpg|jpeg|png))["\']', page_html, re.IGNORECASE)
        if img_match:
            image_url = img_match.group(1)

    clean_desc = re.sub(r'<[^>]+>', ' ', raw_desc)
    clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()

    # افزایش سقف متن تا ۲۵۰۰ کاراکتر برای یک خبر کاملاً مفصل و مشروح
    if len(clean_desc) > 2500:
        clean_desc = clean_desc[:2500] + "..."

    # ترجمه عنوان و متن مفصل
    title_fa = translate_safe(title_en)
    desc_fa = translate_safe(clean_desc)

    # ساخت بخش تصویر و لینک دانلود مستقیم
    image_html = ""
    if image_url:
        image_html = f'''
        <div class="news-image-wrapper" style="margin: 15px 0; text-align: center;">
            <img src="{image_url}" alt="{html.escape(title_fa)}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.15);" />
            <div style="margin-top: 8px;">
                <a href="{image_url}" target="_blank" download rel="noopener noreferrer" style="display: inline-block; background-color: #f0f4f8; color: #0b3d91; padding: 6px 12px; border-radius: 6px; font-size: 0.85rem; text-decoration: none; border: 1px solid #d0d7de;">
                    📥 مشاهده / دانلود مستقیم تصویر با کیفیت اصلی
                </a>
            </div>
        </div>'''
    else:
        image_html = f'''
        <div style="margin: 12px 0; padding: 8px; background-color: #fff9e6; border: 1px dashed #f0ad4e; border-radius: 6px; font-size: 0.85rem; color: #8a6d3b; text-align: center;">
            📷 تصویر درون خبر یافت نشد؛ می‌توانید گالری تصاویر را در <a href="{link_en}" target="_blank" rel="noopener noreferrer" style="color:#0066cc;">صفحه اصلی خبر ناسا</a> مشاهده یا دانلود کنید.
        </div>'''

    news_card_html = f"""<!-- NASA_NEWS_START -->
<div class="news-card" style="direction: rtl; font-family: inherit;">
    <div class="news-header">
        <span class="badge" style="background:#0b3d91; color:#fff; padding:3px 8px; border-radius:4px; font-size:0.8rem;">اخبار نجوم ناسا</span>
        <h3 style="margin-top:10px; line-height:1.5;">{html.escape(title_fa)}</h3>
    </div>
    <div class="news-body">
        {image_html}
        <p class="news-excerpt" style="line-height:2; color:#333; text-align:justify; margin:15px 0; font-size:0.95rem;">{html.escape(desc_fa)}</p>
        <div class="news-meta" style="font-size:0.85rem; color:#666; border-top:1px dashed #ccc; padding-top:8px; margin-top:15px;">
            <span>مترجم: حسین فرحانی</span> | 
            <a href="{link_en}" target="_blank" rel="noopener noreferrer" style="color:#0066cc; text-decoration:none;">مشاهده منبع خبر در NASA</a>
        </div>
    </div>
</div>
<!-- NASA_NEWS_END -->"""

    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"<!-- NASA_NEWS_START -->.*?<!-- NASA_NEWS_END -->"
    if re.search(pattern, content, flags=re.DOTALL):
        new_content = re.sub(pattern, news_card_html, content, flags=re.DOTALL)
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(new_content)
        print("News updated successfully with full article text and image!")
    else:
        print("Warning: markers not found in index.html.")

except Exception as ex:
    print(f"Execution notice: {ex}")
