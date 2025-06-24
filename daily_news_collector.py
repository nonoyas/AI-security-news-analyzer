# daily_news_collector.py (날짜 파싱 실패 시 '오늘'로 간주)

import feedparser
import pandas as pd
import os
from datetime import datetime, timedelta, timezone
import re
import time
from dateutil.parser import parse as date_parse
from pytz import timezone as pytz_timezone

from config import RSS_FEEDS, SECURITY_KEYWORDS, DATA_DIR, LATEST_DAYS

# 한국 시간대 정의
KST = pytz_timezone('Asia/Seoul')


def clean_text(text):
    """HTML 태그 제거 및 공백 정규화"""
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    return ' '.join(text.split())


def is_relevant(title, summary, keywords):
    """제목 또는 요약에 키워드가 포함되어 있는지 확인 (대소문자 구분 없음)"""
    text = (title + " " + summary).lower()
    for keyword in keywords:
        if keyword.lower() in text:
            return True
    return False


def collect_daily_news():
    """매일 RSS 피드를 수집하여 관련 기사를 파일에 저장"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 일일 뉴스 수집 시작...")

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    today_str = datetime.now().strftime('%Y-%m-%d')
    output_filename = os.path.join(DATA_DIR, f"daily_news_{today_str}.csv")

    all_articles = []

    # 현재 시간을 기준으로 비교 임계점 설정 (KST 기준)
    time_threshold = datetime.now(KST) - timedelta(days=LATEST_DAYS)

    for feed_url in RSS_FEEDS:
        is_korean_feed = any(domain in feed_url for domain in
                             ["boannews.com", "dailysecu.com", "ahnlab.com", "estsecurity.com", "krcert.or.kr"])

        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = clean_text(entry.title if hasattr(entry, 'title') else '')
                link = entry.link if hasattr(entry, 'link') else ''
                summary = clean_text(entry.summary if hasattr(entry, 'summary') else '')

                published_date = None

                # 1. feedparser가 파싱한 published_parsed 사용을 1순위로 시도
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        # struct_time을 datetime으로 변환 후 KST로 변환
                        published_date = datetime.fromtimestamp(time.mktime(entry.published_parsed)).astimezone(KST)
                    except Exception as e:
                        # print(f"DEBUG: [Published_parsed] Failed to convert to datetime for '{title[:30]}...' from {feed_url}: {e}")
                        pass  # 실패 시 published 문자열 파싱으로 넘어감

                # 2. published_parsed가 없거나 파싱에 실패하면 published 문자열을 직접 파싱 시도
                if published_date is None and hasattr(entry, 'published') and entry.published:
                    try:
                        parsed = date_parse(entry.published)
                        if parsed.tzinfo is None:  # 시간대 정보가 없으면 KST로 설정
                            published_date = KST.localize(parsed)
                        else:  # 시간대 정보가 있으면 KST로 변환
                            published_date = parsed.astimezone(KST)
                    except Exception as e:
                        # print(f"DEBUG: [Published String] Failed to parse date string for '{title[:30]}...' from {feed_url}: {e}")
                        pass  # 최종 실패 시 published_date는 None으로 남음

                # 3. 날짜 파싱이 최종적으로 실패한 경우, 현재 날짜로 간주하여 일단 수집
                if published_date is None:
                    published_date = datetime.now(KST)  # 현재 KST 시간으로 설정
                    if is_korean_feed:
                        print(f"DEBUG: [국내피드] '{feed_url}' - 제목: '{title[:30]}...' (날짜 파싱 최종 실패! 오늘 날짜로 대체)")

                # DEBUG: 국내 피드의 날짜 파싱 결과 확인 (문제 해결 후 이 디버그 라인들은 삭제 가능)
                if is_korean_feed and published_date:
                    print(f"DEBUG: [국내피드] '{feed_url}' - 제목: '{title[:30]}...'")
                    print(f"DEBUG: published_date (KST): {published_date}, Timezone: {published_date.tzinfo}")
                    print(f"DEBUG: time_threshold (KST): {time_threshold}, Timezone: {time_threshold.tzinfo}")
                    print(f"DEBUG: published_date >= time_threshold: {published_date >= time_threshold}")

                # 발행일이 기준 시간(time_threshold) 이후인지 확인
                if published_date >= time_threshold:  # published_date는 이제 None이 될 일이 없음
                    if is_relevant(title, summary, SECURITY_KEYWORDS):
                        all_articles.append({
                            "Date": published_date.strftime('%Y-%m-%d'),
                            "Time": published_date.strftime('%H:%M:%S'),
                            "Title": title,
                            "Link": link,
                            "Summary": summary,
                            "Source": feed_url
                        })
        except Exception as e:
            print(f"Error collecting from {feed_url}: {e}")

    if all_articles:
        df = pd.DataFrame(all_articles)

        # 파일이 이미 존재하면 기존 데이터에 추가하고 중복 제거
        if os.path.exists(output_filename):
            existing_df = pd.read_csv(output_filename, encoding='utf-8-sig')
            df = pd.concat([existing_df, df]).drop_duplicates(subset=['Title', 'Link']).reset_index(drop=True)

        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"오늘 ({today_str})의 관련 보안 뉴스 {len(df)}건을 '{output_filename}'에 저장했습니다.")
    else:
        print(f"오늘 ({today_str}) 수집된 관련 보안 뉴스가 없습니다.")


if __name__ == "__main__":
    collect_daily_news()