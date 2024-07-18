import os
import pymysql
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import datetime
import time
import re

# 从环境变量中获取配置
api_key = os.getenv('OPENAI_API_KEY')
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# Setup Chrome browser options
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Headless mode
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')

# Launch Chrome browser
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Target URL, replace with actual URL
url = 'https://so.eastmoney.com/news/s?keyword=%E8%B4%B5%E5%B7%9E%E8%8C%85%E5%8F%B0'  # Replace with actual target URL

# Access the page
driver.get(url)

# Wait for the page to load, adjust the time as needed
driver.implicitly_wait(10)

# Get page content
html = driver.page_source

# Parse the page content
soup = BeautifulSoup(html, 'html.parser')

# Find target elements
main_container_div = soup.find('div', class_='main container')
cl_div = main_container_div.find('div', class_='c_l') if main_container_div else None
news_list_div = cl_div.find('div', class_='news_list') if cl_div else None

data = []

if news_list_div:
    news_items = news_list_div.find_all('div', class_='news_item')
    for news_item in news_items:
        # Get date and title
        news_item_c = news_item.find('div', class_='news_item_c')
        if news_item_c:
            time_span = news_item_c.find('span', class_='news_item_time')
            if time_span:
                time_text = time_span.get_text(strip=True)
                # Use regex to extract date and time
                match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', time_text)
                if match:
                    time_text = match.group(0)
                else:
                    time_text = '未知时间'
            else:
                time_text = '未知时间'

            title_spans = news_item_c.find_all('span')
            title_span = title_spans[1] if len(title_spans) > 1 else None
            title_text = title_span.get_text(strip=True) if title_span else '无标题'
        else:
            time_text = '未知时间'
            title_text = '无标题'

        # Find news link
        url_div = news_item.find('div', class_='news_item_url')
        link_tag = url_div.find('a') if url_div else None
        link_url = link_tag['href'] if link_tag else '无链接'

        # Convert time to datetime object for sorting
        try:
            date_dt = datetime.datetime.strptime(time_text, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            print(f"Error parsing date: {time_text}")
            date_dt = None  # Handle invalid date format

        # Get content from the link
        if link_url != '无链接':
            driver.get(link_url)
            driver.implicitly_wait(10)
            inner_html = driver.page_source
            inner_soup = BeautifulSoup(inner_html, 'html.parser')
            content_div = inner_soup.find('div', class_='txtinfos', id='ContentBody')
            content_text = content_div.get_text(strip=True) if content_div else '无内容'

            # Prevent fast access
            time.sleep(2)
        else:
            content_text = '无内容'

        data.append([date_dt, title_text, content_text])

# Close the browser
driver.quit()

# Connect to MySQL database
conn = pymysql.connect(
    host=db_host,    # Replace with your database host
    user=db_user,         # Replace with your database username
    password=db_password,  # Replace with your database password
    database=db_name  # Replace with your database name
)

cursor = conn.cursor()

# Insert data into the database
insert_query = "INSERT INTO news (date, title, content) VALUES (%s, %s, %s)"
cursor.executemany(insert_query, data)

# Commit transaction
conn.commit()

# Fetch unsummarized articles
cursor.execute("SELECT id, content FROM news WHERE summary IS NULL")
articles = cursor.fetchall()

# Function to summarize content
def summarize_content(content):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system",
             "content": "你是茅台AI研究员你会对每一个内容生成一个简洁的文章摘要，专门为贵州茅台公司提供市场趋势、消费者行为、竞争分析和产品改进的深入分析和建议。你的目标是帮助贵州茅台公司在市场上保持竞争力。请根据以下提示进行分析：市场趋势分析:当前全球和国内酒类市场的主要趋势是什么？有哪些新的市场机会和潜在威胁？茅台在这些趋势中的位置如何？消费者行为分析:消费者对茅台产品的偏好和行为模式是什么？社交媒体上关于茅台的讨论热点是什么？销售数据中有哪些值得注意的变化？竞争分析:茅台的主要竞争对手有哪些？竞争对手的市场策略和产品特点是什么？茅台可以从竞争对手那里学到什么？产品改进建议:基于市场和消费者分析，茅台可以如何改进现有产品？有哪些新产品开发的机会？如何提升产品的市场竞争力？品牌管理:茅台的品牌知名度和美誉度如何？有哪些品牌推广和管理的策略建议？如何提升品牌在消费者心中的地位？请根据以上提示进行详细分析，并提供具体的建议和策略"},
            {"role": "user", "content": f"请对以下内容进行总结：\n\n{content}\n"},
        ],
        stream=False
    )
    return response.choices[0].message.content

# Summarize and update each article
for article_id, content in articles:
    summary = summarize_content(content)
    update_query = "UPDATE news SET summary = %s WHERE id = %s"
    cursor.execute(update_query, (summary, article_id))
    conn.commit()

# Close database connection
cursor.close()
conn.close()
