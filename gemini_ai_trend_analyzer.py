import pandas as pd
from pathlib import Path
import os
import google.generativeai as genai
from langdetect import detect, DetectorFactory
from googletrans import Translator # 한국어 번역을 위해 사용
import time # 지연 시간은 여기서는 크게 필요 없지만, 혹시 모를 로드 지연 등에 대비하여 유지

DetectorFactory.seed = 0

# ⚠️ 중요: 실제 사용 시에는 API 키를 환경 변수 등으로 관리하는 것이 훨씬 안전합니다.
API_KEY = ""
genai.configure(api_key=API_KEY)

# 🔹 Gemini 모델 로드 (gemini-1.5-flash 사용)
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    print(f"Gemini 모델 로드 완료: {model.model_name}")
except Exception as e:
    print(f"🚨 Gemini 모델 로드 실패: {e}. API 키 또는 네트워크 상태를 확인하세요.")
    model = None

# 🔹 번역기 로드 (한국어 기사 처리를 위해 필요)
print("번역기 로드 중... (Googletrans)")
try:
    translator = Translator()
    print("번역기 로드 완료.")
except Exception as e:
    print(f"⚠️ 번역기 로드 실패: {e}. 한국어 기사 번역 기능이 작동하지 않을 수 있습니다.")
    translator = None

# 🔹 입력 보고서 폴더 경로
input_report_dir = Path(r"C:\업무\16.뉴스 스크랩(feat.AI.ML)\weekly_reports")

# 🔹 AI 요약 및 인사이트 결과 저장 폴더 경로
output_summary_dir = Path(r"C:\업무\16.뉴스 스크랩(feat.AI.ML)\summarized_outputs")
output_summary_dir.mkdir(parents=True, exist_ok=True) # 폴더가 없으면 생성

# 🔹 최신 CSV 파일 선택
csv_files = list(input_report_dir.glob("*.csv"))
if not csv_files:
    raise FileNotFoundError(f"📂 {input_report_dir} 디렉토리에 CSV 파일이 없습니다.")

target_csv_files = [f for f in csv_files if not f.name.startswith("ai_insight_summary_")]
if not target_csv_files:
    raise FileNotFoundError(f"📂 {input_report_dir} 디렉토리에 'ai_insight_summary_'로 시작하지 않는 원본 CSV 파일이 없습니다.")
latest_file = max(target_csv_files, key=os.path.getmtime)

print(f"📄 최신 입력 파일: {latest_file.name}")

# 🔹 CSV 로드
df = pd.read_csv(latest_file, encoding="utf-8")

# 모든 기사를 처리합니다.
df_to_process = df
print(f"✔️ CSV 파일에서 총 {len(df_to_process)}개 기사를 검토합니다.")

# 모든 기사의 내용을 하나의 큰 텍스트로 합칠 리스트
all_articles_combined_text = []

if model is None:
    print("🚨 Gemini 모델이 로드되지 않아 프로세스를 계속할 수 없습니다. 실행을 중단합니다.")
else:
    print("\n--- 모든 기사 내용 취합 및 번역 시작 ---")
    for idx, row in df_to_process.iterrows():
        title = str(row.get("Title", "")).strip()
        content = str(row.get("Summary", "")).strip()

        if not content or len(content) < 30:
            # print(f"  🚨 기사 {idx+1} 건너뛰기: 내용이 없거나 30자 미만입니다.")
            continue

        processed_content_en = ""
        try:
            lang = detect(content)
            # print(f"  ➡️ 기사 {idx+1} 감지된 언어: {lang.upper()}")

            if lang == 'ko':
                if translator:
                    processed_content_en = translator.translate(content, dest='en').text
                else:
                    # print("  ⚠️ 번역기 로드 실패로 한국어 기사를 처리할 수 없습니다. 건너뜁니다.")
                    continue
            elif lang == 'en':
                processed_content_en = content
            else:
                # print(f"  🚫 기사 {idx+1} 건너뛰기: 영어/한국어 기사가 아닙니다 (감지된 언어: {lang}).")
                continue

            # 합쳐질 텍스트 형식: "--- Article [번호] ---\nTitle: [제목]\nBody: [내용]\n\n"
            all_articles_combined_text.append(f"--- Article {idx+1} ---\nTitle: {title}\nBody: {processed_content_en}\n")

        except Exception as e:
            print(f"  ⚠️ 기사 {idx+1} 언어 감지/번역 실패 ({e}), 건너뜁니다.")
            continue
    print("--- 모든 기사 내용 취합 및 번역 완료 ---")

    # 🔹 상위 레벨 종합 인사이트 도출 로직 (단 1회 호출) ---
    print("\n--- 상위 레벨 종합 인사이트 도출 시작 (Gemini 1회 호출) ---")

    # 모든 취합된 기사 내용을 하나의 큰 텍스트로 결합
    overall_input_text = "\n\n".join(all_articles_combined_text)

    # 입력 텍스트가 비어 있거나 너무 짧으면 스킵
    if not overall_input_text or len(overall_input_text) < 100:
        overall_summary = "처리할 기사 내용이 부족하여 상위 레벨 종합 인사이트를 생성할 수 없습니다."
        print(overall_summary)
    else:
        # Gemini 모델에 입력할 프롬프트 생성
        prompt_for_overall_insight = (
            f"The following is a collection of recent cybersecurity news articles. Each article is separated by '--- Article [번호] ---'.\n\n"
            f"{overall_input_text}\n\n"
            f"Based on all these articles, provide a comprehensive overview of the current cybersecurity landscape, "
            f"major trends, and key implications for the industry. "
            f"Group similar points and synthesize them into 3-5 concise, actionable paragraphs. "
            f"Structure your response with clear headings (e.g., '1. [Trend Name]'). "
            f"For each major trend, within the 'Insight' section, connect the insight with specific, factual examples or relevant entities/events mentioned in the provided articles. "  # <-- 이 줄 수정
            f"Start with a strong summary sentence, then use bullet points or numbered lists for the main insights. "
            f"Ensure the 'Insight' section directly references real-world events or named entities from the articles to illustrate the point. "  # <-- 이 줄 추가
            f"Provide an overall conclusion or outlook."
        )
        overall_summary = ""
        try:
            print("  Gemini 상위 레벨 종합 인사이트 추출 중 (단 1회 API 호출)...")
            response = model.generate_content(prompt_for_overall_insight)
            overall_summary = response.text.strip()
            print("  ✅ 상위 레벨 종합 인사이트 추출 완료.")

        except Exception as e:
            overall_summary = f"(상위 레벨 종합 인사이트 추출 실패: {e})"
            print(f"  ❌ 상위 레벨 종합 인사이트 추출 실패: {e}. 오류: {e}")
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                print("    ➡️ 할당량/속도 제한 오류 감지. 다음날 다시 시도하거나 할당량 확인 필요.")

    # 🔹 상위 레벨 종합 인사이트 결과 저장 🔹
    overall_insight_output_file = output_summary_dir / f"ai_overall_insights_single_call_{latest_file.stem}_gemini_flash.txt" # 파일명 변경
    with open(overall_insight_output_file, "w", encoding="utf-8") as f:
        f.write("--- 상위 레벨 종합 사이버 보안 인사이트 (Gemini Flash API, 단일 호출) ---\n\n")
        f.write(overall_summary)
        f.write("\n\n--- End of Overall Insights ---")

    print(f"\n🎉 상위 레벨 종합 인사이트 보고서 저장 완료: {overall_insight_output_file}")
    print("\nAI 인사이트 도출 프로세스가 완료되었습니다.")
