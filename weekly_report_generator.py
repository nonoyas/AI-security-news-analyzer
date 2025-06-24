# weekly_report_generator.py

import pandas as pd
import os
from datetime import datetime, timedelta
from config import DATA_DIR, WEEKLY_REPORT_DIR, WEEKLY_REPORT_DAYS


def generate_weekly_report():
    """
    일별 수집된 CSV 파일들을 취합하여 주간 보고서 CSV 파일을 생성합니다.
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 주간 보고서 생성 시작...")

    # 주간 보고서 저장 폴더 생성 (없으면)
    if not os.path.exists(WEEKLY_REPORT_DIR):
        os.makedirs(WEEKLY_REPORT_DIR)

    all_weekly_articles = []

    # 보고서 생성 기준 날짜 (오늘부터 WEEKLY_REPORT_DAYS 이전까지)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=WEEKLY_REPORT_DAYS)

    print(f"기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

    # 지정된 기간 내의 모든 일별 CSV 파일 읽기
    for i in range(WEEKLY_REPORT_DAYS + 1):  # 시작일 포함
        current_date = start_date + timedelta(days=i)
        filename = os.path.join(DATA_DIR, f"daily_news_{current_date.strftime('%Y-%m-%d')}.csv")

        if os.path.exists(filename):
            try:
                df_daily = pd.read_csv(filename, encoding='utf-8-sig')
                all_weekly_articles.append(df_daily)
                print(f"  -> '{filename}' 파일 로드 완료.")
            except pd.errors.EmptyDataError:
                print(f"  -> '{filename}' 파일은 비어있습니다. 건너뜝니다.")
            except Exception as e:
                print(f"  -> '{filename}' 파일을 로드하는 중 오류 발생: {e}")
        # else:
        #     print(f"  -> '{filename}' 파일이 존재하지 않습니다. 건너뜝니다.") # 너무 많으면 주석처리

    if not all_weekly_articles:
        print("수집된 일별 뉴스 파일이 없어 주간 보고서를 생성할 수 없습니다.")
        return

    # 모든 일별 데이터를 하나의 DataFrame으로 합치기
    df_combined = pd.concat(all_weekly_articles, ignore_index=True)

    # 중복 제거 (제목과 링크가 완전히 동일한 경우만)
    df_combined.drop_duplicates(subset=['Title', 'Link'], inplace=True)

    # 발행일 기준으로 정렬
    # 'Date'와 'Time' 컬럼을 합쳐 datetime 객체로 변환하여 정확히 정렬
    df_combined['FullDateTime'] = pd.to_datetime(df_combined['Date'] + ' ' + df_combined['Time'], errors='coerce')
    df_combined.sort_values(by='FullDateTime', ascending=False, inplace=True)
    df_combined.drop(columns=['FullDateTime'], inplace=True)  # 정렬 후 임시 컬럼 삭제

    # 주간 보고서 파일명 정의 (가장 최근 날짜 기준)
    output_weekly_filename = os.path.join(WEEKLY_REPORT_DIR,
                                          f"weekly_security_report_{end_date.strftime('%Y-%m-%d')}.csv")

    df_combined.to_csv(output_weekly_filename, index=False, encoding='utf-8-sig')
    print(f"주간 보고서 생성 완료: 총 {len(df_combined)}건의 뉴스가 '{output_weekly_filename}'에 저장되었습니다.")


if __name__ == "__main__":
    generate_weekly_report()