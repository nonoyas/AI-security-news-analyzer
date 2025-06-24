# config.py

# 국내외 보안 뉴스 RSS 피드 URL 목록
RSS_FEEDS = [
    # 국내 (Korean) - PM님께서 찾아주신 새로운 피드들
    "http://www.boannews.com/media/news_rss.xml?mkind=1", # 보안뉴스 - 주요 뉴스
    "http://www.boannews.com/media/news_rss.xml?kind=1",  # 보안뉴스 - 보안 정책
    "http://www.boannews.com/media/news_rss.xml?kind=4",  # 보안뉴스 - 산업 동향
    "http://www.boannews.com/media/news_rss.xml?skind=5", # 보안뉴스 - IT 보안
    "https://knvd.krcert.or.kr/rss/securityInfo.do",      # KISA - 보안 정보 (취약점 공지 등)
    "https://knvd.krcert.or.kr/rss/securityNotice.do",    # KISA - 보안 공지
    "https://www.dailysecu.com/rss/allArticle.xml",       # 데일리시큐 - 전체 기사

    # 해외 (International) - 기존 피드 유지
    "https://feeds.feedburner.com/TheHackersNews", # The Hacker News (글로벌 보안 위협 전반)
    "https://krebsonsecurity.com/feed/",          # KrebsOnSecurity (심층 분석, 사이버 범죄)
    "https://www.bleepingcomputer.com/feed/",     # BleepingComputer (랜섬웨어, 악성코드 등 기술적 분석)
    "https://us-cert.cisa.gov/ncas/all.xml",       # CISA (미국 정부기관의 취약점 및 경고)
    "https://www.darkreading.com/rss_simple.xml",  # Dark Reading (엔터프라이즈 보안, 산업 동향)
    "https://isc.sans.edu/rss.xml"                # SANS Internet Storm Center (일일 위협 분석)
]

# 검색할 보안 키워드 목록 (대소문자 구분 없음)
SECURITY_KEYWORDS = [
    "랜섬웨어", "Ransomware", "다크웹", "Darkweb", "APT", "Advanced Persistent Threat",
    "제로데이", "Zero-day", "취약점", "Vulnerability", "익스플로잇", "Exploit",
    "해킹", "Hacking", "침해사고", "Breach", "정보유출", "Data Breach", "데이터 유출", "Data Leak",
    "피싱", "Phishing", "스피어피싱", "Spear Phishing", "악성코드", "Malware", "트로이 목마", "Trojan", "바이러스", "Virus",
    "디도스", "DDoS", "서비스 거부", "Denial of Service",
    "공급망 공격", "Supply Chain Attack",
    "스캠", "Scam", "사기", "Fraud",
    "보안 업데이트", "Security Update", "패치", "Patch", "보안 권고", "Security Advisory", "CISA",
    "클라우드 보안", "Cloud Security", "OT 보안", "OT Security", "ICS 보안", "ICS Security", "산업 제어 시스템", "Industrial Control System",
    "AI 보안", "AI Security", "머신러닝 보안", "Machine Learning Security",
    "보안 인증", "Security Certification", "GDPR", "개인정보보호", "Privacy", "PII", "Personally Identifiable Information",
    "규제", "Regulation", "법률", "Law", "가이드라인", "Guideline",
    "사이버 안보", "Cybersecurity", "국가 안보", "National Security",
    "아동 성착취물", "CSAM", "아동 음란물", "Child Pornography",
    "다크 패턴", "Dark Patterns", "불법 광고"
]

# 1단계: 일일 데이터 저장 경로 (현재 스크립트 파일이 있는 폴더 기준)
DATA_DIR = "security_news_data"

# 1단계: 뉴스 수집 기준: 현재 시간으로부터 LATEST_DAYS 이내에 발행된 기사만 수집
# 일반적으로 2일 정도면 어제/오늘 기사를 충분히 커버하며, 업데이트 주기가 느린 피드도 포괄 가능
LATEST_DAYS = 2

# 2단계: 주간 보고서 저장 경로 (현재 스크립트 파일이 있는 폴더 기준)
WEEKLY_REPORT_DIR = "weekly_reports"

# 2단계: 주간 보고서 취합 기준: 최근 몇 일간의 데이터를 취합할 것인지 설정 (예: 7일)
WEEKLY_REPORT_DAYS = 7

# 3단계: AI 분석 보고서 저장 경로 (현재 스크립트 파일이 있는 폴더 기준)
AI_ANALYSIS_REPORT_DIR = "ai_analysis_reports"