import pandas as pd
from transformers import pipeline
from pathlib import Path
import os
import torch
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0

# 🔹 요약 모델 (영어 요약에 특화된 모델 사용)
device = -1
print("영어 요약 모델 로드 중... (facebook/bart-large-cnn)")
summarizer_en = pipeline("summarization", model="facebook/bart-large-cnn", device=device)
print("영어 요약 모델 로드 완료.")

# 🔹 입력 보고서 폴더 경로 (원본 데이터가 있는 곳)
# 이 폴더에서 가장 최신 CSV 파일을 찾습니다.
input_report_dir = Path(r"C:\업무\16.뉴스 스크랩(feat.AI.ML)\weekly_reports")

# 🔹 AI 요약 결과 저장 폴더 경로 (새로 생성하거나 지정)
# 이 폴더에 AI 요약 결과 CSV 파일이 저장됩니다.
output_summary_dir = Path(r"C:\업무\16.뉴스 스크랩(feat.AI.ML)\summarized_outputs")
output_summary_dir.mkdir(parents=True, exist_ok=True)  # 폴더가 없으면 생성

# 🔹 최신 CSV 선택 (입력 폴더에서만)
csv_files = list(input_report_dir.glob("*.csv"))  # input_report_dir에서만 찾기
if not csv_files:
    raise FileNotFoundError(f"📂 {input_report_dir} 디렉토리에 CSV 파일이 없습니다.")

# 여기서 `weekly_security_report_2025-06-25.csv` 와 같은 원본 파일을 정확히 찾으려면
# 파일 이름 패턴을 더 명확히 하거나 (예: starts with 'weekly_security_report_')
# 또는 단순히 가장 오래된 파일이 아닌, 특정 패턴을 가진 가장 최신 파일을 선택하는 로직이 필요할 수 있습니다.
# 일단은 'ai_insight_summary_' 로 시작하지 않는 파일 중 가장 최신 파일을 선택하도록 수정합니다.
target_csv_files = [f for f in csv_files if not f.name.startswith("ai_insight_summary_")]
if not target_csv_files:
    raise FileNotFoundError(f"📂 {input_report_dir} 디렉토리에 'ai_insight_summary_'로 시작하지 않는 원본 CSV 파일이 없습니다.")
latest_file = max(target_csv_files, key=os.path.getmtime)

print(f"📄 최신 입력 파일: {latest_file.name}")  # 입력 파일임을 명시

# 🔹 CSV 로드
df = pd.read_csv(latest_file, encoding="utf-8")

df_to_process = df.head(6)
print(f"✔️ CSV 파일에서 상위 {len(df_to_process)}개 기사를 검토합니다.")

output = []
processed_count = 0

for idx, row in df_to_process.iterrows():
    title = str(row.get("Title", "")).strip()
    content = str(row.get("Summary", "")).strip()

    print(f"\n--- {idx + 1}번째 기사 처리 중: '{title[:50]}...' ---")

    if not content or len(content) < 30:
        print(f"  🚨 건너뛰기: 내용이 없거나 30자 미만입니다.")
        continue

    # 1. 언어 감지
    try:
        lang = detect(content)
        print(f"  ➡️ 감지된 언어: {lang.upper()}")
    except Exception as e:
        lang = 'unknown'
        print(f"  ⚠️ 언어 감지 실패 ({e}), 건너뜁니다.")
        continue

    # 2. 영어 기사가 아니면 건너뛰기
    if lang != 'en':
        print(f"  🚫 건너뛰기: 영어 기사가 아닙니다.")
        continue

    # 3. 영어 요약 모델에 입력할 프롬프트 생성 (인사이트 추출 강조)
    input_text = f"Title: {title}\n\nBody: {content}\n\nBased on the above news summary, describe the emerging trend or significant shift in the cybersecurity landscape in two concise sentences."

    try:
        print("  AI 인사이트 추출 중...")
        insight_summary = summarizer_en(input_text, max_length=60, min_length=20, do_sample=False)[0]["summary_text"]
        print("  ✅ 인사이트 추출 완료.")
        processed_count += 1
    except Exception as e:
        insight_summary = f"(Insight extraction failed: {e})"
        print(f"  ❌ 인사이트 추출 실패: {e}")

    output.append({
        "title": title,
        "summary": content,
        "ai_insight": insight_summary,
        "url": row.get("Link", ""),
        "source": row.get("Source", "")
    })

# 🔹 결과 확인
print(f"\n✅ 총 인사이트 추출 완료: {processed_count}건")

# 🔹 결과 저장 🔹
output_df = pd.DataFrame(output)
# 결과를 새로운 폴더에 저장하도록 경로 변경
output_df.to_csv(output_summary_dir / f"ai_insight_summary_{latest_file.stem}_en_only.csv", index=False,
                 encoding="utf-8-sig")
print(f"\n🎉 AI 인사이트 요약 보고서 저장 완료: {output_summary_dir / f'ai_insight_summary_{latest_file.stem}_en_only.csv'}")
