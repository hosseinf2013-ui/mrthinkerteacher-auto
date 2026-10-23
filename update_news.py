import urllib.request
import xml.etree.ElementTree as ET
import re
import html
from deep_translator import GoogleTranslator

NASA_RSS_URL = "https://www.nasa.gov/news-release/feed/"

headers = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request(NASA_RSS_URL, headers=headers)
response = urllib.request.urlopen(req)
xml_data = response.read()

root = ET.fromstring(xml_data)
channel = root.find('channel')
latest_item = channel.find('item')

title_en = latest_item.find('title').text
link_en = latest_item.find('link').text
desc_en = latest_item.find('description').text if latest_item.find('description') is not None else ""

clean_desc = re.sub(r'<[^>]+>', '', desc_en).strip()
if len(clean_desc) > 800:
    clean_desc = clean_desc[:800] + "..."

translator = GoogleTranslator(source='en', target='fa')
title_fa = translator.translate(title_en)
desc_fa = translator.translate(clean_desc)

news_card_html = f"""<!-- NASA_NEWS_START -->
<div class="news-card">
    <div class="news-header">
        <span class="badge">نجوم</span>
        <h3>{html.escape(title_fa)}</h3>
    </div>
    <div class="news-body">
        <p class="news-excerpt" style="line-height:1.8; color:#333; text-align:justify; margin:10px 0;">{html.escape(desc_fa)}</p>
        <div class="news-meta" style="font-size:0.85rem; color:#666; border-top:1px dashed #ccc; padding-top:8px; margin-top:10px;">
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
    print("News updated successfully!")
else:
    print("Markers not found!")
