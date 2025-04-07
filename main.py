import discord
import feedparser
import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# 1. 환경변수 불러오기
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_IDS = {
    "IT": int(os.getenv("IT_CHANNEL_ID")),
    "DEV": int(os.getenv("DEV_CHANNEL_ID")),
    "GAME": int(os.getenv("GAME_CHANNEL_ID")),
    "DESIGN": int(os.getenv("DESIGN_CHANNEL_ID"))
}

# 2. 클라이언트 생성
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# 3. 누적 뉴스 저장소
posted_links = set()

# 4. RSS 주소 로드
with open("rss_urls.json", "r") as f:
    RSS_FEEDS = json.load(f)

# 5. 요약 함수 (앞 문장 150자)
def summarize(text):
    return text.strip().replace("\n", " ")[:150] + "..."

# 6. 뉴스 가져오기
def fetch_top_news(category):
    feeds = RSS_FEEDS[category]
    top_news = None
    top_views = -1

    for url in feeds:
        d = feedparser.parse(url)
        for entry in d.entries:
            if entry.link in posted_links:
                continue

            views = 0  # 조회수가 있다면 여기에 처리
            if top_news is None or views > top_views:
                top_news = entry
                top_views = views

    return top_news

# 7. 매시 정각에 실행
async def news_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        now = datetime.now()
        if now.minute == 0:
            for category, channel_id in CHANNEL_IDS.items():
                news = fetch_top_news(category)
                if news:
                    summary = summarize(news.get("summary", news.get("description", "")))
                    msg = f"**{news.title}**\n{summary}\n<{news.link}>"
                    channel = client.get_channel(channel_id)
                    await channel.send(msg)
                    posted_links.add(news.link)
            await asyncio.sleep(60)  # 1분 대기
        else:
            await asyncio.sleep(10)

# 8. 봇 시작
@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}')
    client.loop.create_task(news_loop())

client.run(TOKEN)
