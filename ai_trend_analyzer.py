# ai_trend_analyzer.py (모델 직접 제어 버전)

import pandas as pd
import os
from datetime import datetime, timedelta
# from transformers import pipeline # pipeline 대신 개별 모듈 임포트
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM  # KoBART 모델을 위한 클래스
import torch  # PyTorch 텐서 처리를 위해 필요

import config  # config 모듈 전체를 임포트

# -----------------------------------------------------------------------------
# 1. 모델 및 토크나이저 로드 (한국어 요약 모델)
# -----------------------------------------------------------------------------
print("AI 모델 및 토크나이저 로드 중... (시간이 다소 소요될 수 있습니다)")
try:
    # 모델과 토크나이저를 직접 로드합니다.
    model_name = "gogamza/kobart-base-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    # GPU 사용 가능 여부 확인
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)  # 모델을 CPU 또는 GPU로 이동
    print(f"Device set to use {device}")

    print(f"AI 요약 모델 로드 완료: {model_name}")

except Exception as e:
    print(f"AI 모델 로드 실패: {e}")
    print("오류 코드: `gogamza/kobart-base-v2` 모델을 로드할 수 없습니다.")
    print("1. 인터넷 연결 상태를 확인해주세요.")
    print("2. `pip install transformers sentencepiece torch` (또는 tensorflow) 명령어가 올바르게 실행되었는지 확인해주세요.")
    print("3. GPU 사용 시 PyTorch 공식 사이트에서 자신의 CUDA 버전에 맞는 PyTorch 설치 명령어를 다시 확인해주세요.")
    tokenizer = None
    model = None


def analyze_and_summarize_news():
    """
    주간 보고서 CSV를 분석하여 핵심 트렌드를 감지하고 요약문을 생성합니다.
    """
    if tokenizer is None or model is None:  # 모델 로드 실패 시 분석 진행 불가
        print("AI 모델이 로드되지 않아 분석을 진행할 수 없습니다.")
        return

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AI 기반 트렌드 분석 시작...")

    # AI 분석 보고서 저장 폴더 생성 (없으면)
    if not os.path.exists(config.AI_ANALYSIS_REPORT_DIR):
        os.makedirs(config.AI_ANALYSIS_REPORT_DIR)

    # 가장 최근의 주간 보고서 파일 찾기
    weekly_files = [f for f in os.listdir(config.WEEKLY_REPORT_DIR) if
                    f.startswith("weekly_security_report_") and f.endswith(".csv")]
    if not weekly_files:
        print(f"'{config.WEEKLY_REPORT_DIR}' 폴더에 주간 보고서 파일이 없습니다. 먼저 2단계 스크립트를 실행하여 주간 보고서를 생성해주세요.")
        return

    # 최신 파일을 찾아 로드
    latest_weekly_file = max(weekly_files,
                             key=lambda f: datetime.strptime(f.split('_')[-1].replace('.csv', ''), '%Y-%m-%d'))
    input_filepath = os.path.join(config.WEEKLY_REPORT_DIR, latest_weekly_file)

    print(f"'{input_filepath}' 파일을 로드하여 분석합니다.")
    try:
        df_weekly = pd.read_csv(input_filepath, encoding='utf-8-sig')
        if df_weekly.empty:
            print("주간 보고서 파일이 비어 있습니다. 분석할 내용이 없습니다.")
            return
    except Exception as e:
        print(f"주간 보고서 파일 로드 중 오류 발생: {e}")
        return

    # -------------------------------------------------------------------------
    # 3. 핵심 트렌드 감지 및 요약
    # -------------------------------------------------------------------------
    all_news_text = ""
    MAX_INPUT_TEXT_LENGTH = 3000  # 한글 3000자면 대략 1024 토큰 근처 (보수적)

    for index, row in df_weekly.iterrows():
        article_text = f"제목: {row['Title']}. 요약: {row['Summary']}."

        if len(all_news_text) + len(article_text) > MAX_INPUT_TEXT_LENGTH:
            all_news_text += " [내용이 길어 일부만 요약에 사용됨]"
            break
        all_news_text += article_text + " "

    generated_summary = "AI 요약문 생성에 실패했습니다: 분석할 텍스트가 부족하거나, 모델 처리 중 오류 발생."
    MIN_VALID_TEXT_LENGTH = 50

    if len(all_news_text.strip()) < MIN_VALID_TEXT_LENGTH:
        print(f"분석할 텍스트가 너무 짧습니다 ({len(all_news_text.strip())}자). 요약을 건너뜜.")
    else:
        print("뉴스 요약문 생성 중...")
        try:
            # 텍스트를 토크나이징하고 모델이 이해할 수 있는 형태로 변환
            # truncation=True: 최대 길이를 넘으면 자동으로 잘라냄
            # return_tensors="pt": PyTorch 텐서로 반환
            inputs = tokenizer(
                all_news_text,
                return_tensors="pt",
                truncation=True,
                max_length=1024  # KoBART 모델의 최대 입력 길이
            ).to(device)  # 입력 텐서를 모델과 동일한 디바이스로 이동

            # 모델의 generate 함수를 사용하여 요약문 생성
            # max_length: 생성될 요약문의 최대 토큰 길이
            # min_length: 생성될 요약문의 최소 토큰 길이
            # num_beams: 빔 서치(beam search) 개수. 높을수록 고품질 요약 가능하나 느려짐.
            # early_stopping: 빔 서치 조기 종료 여부
            summary_ids = model.generate(
                inputs["input_ids"],
                max_length=250,
                min_length=50,
                num_beams=5,  # 일반적으로 3~5가 좋음
                early_stopping=True
            )

            # 생성된 토큰 ID를 다시 텍스트로 디코딩
            # skip_special_tokens=True: [CLS], [SEP] 같은 특수 토큰 제거
            generated_summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

            print("\n--- 주간 보안 동향 요약 (AI 생성 초안) ---")
            print(generated_summary)
            print("-------------------------------------------\n")

        except Exception as e:
            # 오류 발생 시 디버깅을 돕기 위해 에러 메시지와 함께 원본 텍스트 일부를 포함
            generated_summary = f"AI 요약문 생성 중 오류 발생: {e}. 원본 텍스트 시작: '{all_news_text[:200]}...'"
            print(generated_summary)  # 콘솔에도 출력

    # -------------------------------------------------------------------------
    # 4. 결과 저장
    # -------------------------------------------------------------------------
    end_date_str = latest_weekly_file.split('_')[-1].replace('.csv', '')
    end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d')
    start_date_obj = end_date_obj - timedelta(days=config.WEEKLY_REPORT_DAYS - 1)

    df_analysis = pd.DataFrame({
        "Analysis_Date": [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        "Report_Period": [f"{start_date_obj.strftime('%Y-%m-%d')} ~ {end_date_obj.strftime('%Y-%m-%d')}"],
        "AI_Generated_Summary": [generated_summary],
        "Source_Weekly_Report": [latest_weekly_file]
    })

    output_analysis_filename = os.path.join(config.AI_ANALYSIS_REPORT_DIR,
                                            f"ai_security_trend_report_{end_date_obj.strftime('%Y-%m-%d')}.csv")

    df_analysis.to_csv(output_analysis_filename, index=False, encoding='utf-8-sig')
    print(f"AI 분석 결과가 '{output_analysis_filename}'에 저장되었습니다.")


if __name__ == "__main__":
    if not os.path.exists(config.WEEKLY_REPORT_DIR):
        print(f"오류: 주간 보고서 폴더 '{config.WEEKLY_REPORT_DIR}'가 존재하지 않습니다. 2단계 스크립트를 먼저 실행하여 보고서를 생성해주세요.")
    else:
        analyze_and_summarize_news()