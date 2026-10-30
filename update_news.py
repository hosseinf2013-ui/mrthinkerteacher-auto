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
    # تلاش اول: Google Translator با تاخیر امن
    try:
        time.sleep(1)
        return GoogleTranslator(source='en', target='fa').translate(text)
    except Exception as e:
        print(f"Google translate limit hit: {e}. Trying fallback...")
    
    # تلاش دوم: MyMemory Translator به عنوان پشتیبان
    try:
        time.sleep(1)
        return MyMemoryTranslator(source='en-US', target='fa-IR').translate(text)
    except Exception as e:
        print(f"Fallback translation error: {e}")
        return text  # در صورت قطعی هر دو سرویس، متن اصلی انگلیسی قرار گیرد

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

    # ۱. استخراج تصویر از تگ enclosure یا ویژگی‌های دیگر
    image_url = ""
    enclosure = latest_item.find('enclosure')
    if enclosure is not None and 'url' in enclosure.attrib:
        image_url = enclosure.attrib['url']
    else:
        for child in latest_item:
            if 'url' in child.attrib and child.attrib.get('type', '').startswith('image'):
                image_url = child.attrib['url']
                break

    # ۲. استخراج متن مفصل‌تر
    namespaces = {'content': 'http://purl.org/rss/1.0/modules/content/'}
    content_encoded = latest_item.find('content:encoded', namespaces)

    if content_encoded is not None and content_encoded.text:
        raw_desc = content_encoded.text
    elif latest_item.find('description') is not None:
        raw_desc = latest_item.find('description').text
    else:
        raw_desc = ""

    # اگر تصویر در تگ‌های بالا نبود، از داخل تگ img متن استخراج شود
    if not image_url:
        img_match = re.search(r'<img[^>]+src=["\'](.*?)["\']', raw_desc)
        if img_match:
            image_url = img_match.group(1)

    clean_desc = re.sub(r'<[^>]+>', ' ', raw_desc)
    clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()

    # افزایش سقف متن تا ۱۵۰۰ کاراکتر
    if len(clean_desc) > 1500:
        clean_desc = clean_desc[:1500] + "..."

    # ۳. ترجمه عنوان و متن
    title_fa = translate_safe(title_en)
    desc_fa = translate_safe(clean_desc)

    # ۴. ساخت بخش تصویر همراه با لینک دانلود مستقیم
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
        # در صورتی که تصویری پیدا نشد، لینک خود خبر در ناسا برای بررسی گالری داده می‌شود
        image_html = f'''
        <div style="margin: 12px 0; padding: 8px; background-color: #fff9e6; border: 1px dashed #f0ad4e; border-radius: 6px; font-size: 0.85rem; color: #8a6d3b; text-align: center;">
            📷 تصویر درون فید یافت نشد؛ می‌توانید گالری تصاویر را در <a href="{link_en}" target="_blank" rel="noopener noreferrer" style="color:#0066cc;">صفحه اصلی خبر ناسا</a> مشاهده یا دانلود کنید.
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
        print("News updated successfully with image and download link!")
    else:
        print("Warning: markers not found in index.html.")

except Exception as ex:
    print(f"Execution notice: {ex}")
