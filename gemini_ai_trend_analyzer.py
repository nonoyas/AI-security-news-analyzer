import pandas as pd
from pathlib import Path
import os
import google.generativeai as genai
from langdetect import detect, DetectorFactory
from googletrans import Translator 
import time 

DetectorFactory.seed = 0

API_KEY = ""
genai.configure(api_key=API_KEY)

try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    print(f"Gemini 모델 로드 완료: {model.model_name}")
except Exception as e:
    print(f"🚨 Gemini 모델 로드 실패: {e}. API 키 또는 네트워크 상태를 확인하세요.")
    model = None

print("번역기 로드 중... (Googletrans)")
try:
    translator = Translator()
    print("번역기 로드 완료.")
except Exception as e:
    print(f"⚠️ 번역기 로드 실패: {e}. 한국어 기사 번역 기능이 작동하지 않을 수 있습니다.")
    translator = None

input_report_dir = Path(r"C:\업무\16.뉴스 스크랩(feat.AI.ML)\weekly_reports")

output_summary_dir = Path(r"C:\업무\16.뉴스 스크랩(feat.AI.ML)\summarized_outputs")
output_summary_dir.mkdir(parents=True, exist_ok=True)

csv_files = list(input_report_dir.glob("*.csv"))
if not csv_files:
    raise FileNotFoundError(f"📂 {input_report_dir} 디렉토리에 CSV 파일이 없습니다.")

target_csv_files = [f for f in csv_files if not f.name.startswith("ai_insight_summary_")]
if not target_csv_files:
    raise FileNotFoundError(f"📂 {input_report_dir} 디렉토리에 'ai_insight_summary_'로 시작하지 않는 원본 CSV 파일이 없습니다.")
latest_file = max(target_csv_files, key=os.path.getmtime)

print(f"📄 최신 입력 파일: {latest_file.name}")

df = pd.read_csv(latest_file, encoding="utf-8")

df_to_process = df
print(f"✔️ CSV 파일에서 총 {len(df_to_process)}개 기사를 검토합니다.")

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

    print("\n--- 상위 레벨 종합 인사이트 도출 시작 (Gemini 1회 호출) ---")

    overall_input_text = "\n\n".join(all_articles_combined_text)

    if not overall_input_text or len(overall_input_text) < 100:
        overall_summary = "처리할 기사 내용이 부족하여 상위 레벨 종합 인사이트를 생성할 수 없습니다."
        print(overall_summary)
    else:
        prompt_for_overall_insight = (
            f"**[CRITICAL] ABSOLUTELY DO NOT include 'Article [Number]' or any similar numerical reference to articles in the generated analysis. This is a strict requirement for a professional client report.**\n"
            f"**[RE-EMPHASIS] All insights and examples must refer directly to specific entities, events, or attack types mentioned in the provided articles, WITHOUT citing their article numbers.**\n\n"
            f"The following is a collection of recent cybersecurity news articles. Each article is separated by '--- Article [번호] ---'.\n\n"
            f"{overall_input_text}\n\n"
            f"Based on all these articles, provide a comprehensive overview of the current cybersecurity landscape, "
            f"major trends, and key implications for the industry. "
            f"Group similar points and synthesize them into clear sections. "
            f"Structure your response with clear headings (e.g., '1. [Trend Name]'). "
            f"**Each major trend chapter must be at least twice the current length, providing detailed analysis.**\n"
            f"**For each 'Insight' section, go beyond merely listing phenomena. Deeply analyze and incorporate the following aspects:**\n"
            f"* **Diverse related cases and patterns inferable from them.**\n"
            f"* **The practical impact and ripple effects of the trend on the industry as a whole.**\n"
            f"* **Specific risks and challenges arising from this trend.**\n"
            f"* **Current limitations in security responses and additional considerations needed.**\n"
            f"* **Future predictions and potential scenarios.**\n"
            f"For each major trend, within the '인사이트' section, clearly analyze its positive, neutral aspects, as well as its potential risks, limitations, and unresolved issues. Connect these insights with specific, factual examples or relevant entities/events mentioned in the provided articles. "
            f"Start with a strong summary sentence, then use bullet points or numbered lists for the main insights. "
            f"Ensure the '인사이트' section directly references real-world events or named entities from the articles to illustrate the point. "
            f"Specifically, go beyond the surface of the articles to deeply analyze and highlight hidden meanings, potential risks, and fundamental unresolved problems within the cybersecurity environment, utilizing critical thinking. This analysis should provide comprehensive insights, not just a mere enumeration."
            f"\n\n**CAUTION:** All analysis and insights must be strictly based ONLY on the content of the 80 articles provided above. Take extreme care to prevent hallucinations by not adding external information or facts not present in the articles."
            f"\n\n**Exclude the 'Conclusion' section from the report. The report should consist only of the introduction and the major trend chapters.**"
            f"\n\n**All responses must be written in Korean. Ensure the Korean context and expressions are as natural and professional as a specialized report.**"
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

    overall_insight_output_file = output_summary_dir / f"ai_overall_insights_single_call_{latest_file.stem}_gemini_flash.txt" # 파일명 변경
    with open(overall_insight_output_file, "w", encoding="utf-8") as f:
        f.write(overall_summary)
        f.write("\n\n--- End of Overall Insights ---")

    print(f"\n🎉 상위 레벨 종합 인사이트 보고서 저장 완료: {overall_insight_output_file}")
    print("\nAI 인사이트 도출 프로세스가 완료되었습니다.")
