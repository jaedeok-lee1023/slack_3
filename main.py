import os
import sys
import datetime
import arrow
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from kurly import clusters

# 🎯 한국 공휴일 목록 (YYYY-MM-DD 형식)
HOLIDAYS = {
    "2025-01-01",  # 신정
    "2025-03-01",  # 삼일절
    "2025-05-05",  # 어린이날
    "2025-05-06",  # 대체공휴일
    "2025-06-02",  # 대체공휴일
    "2025-06-03",  # 선거일
    "2025-06-06",  # 현충일
    "2025-08-15",  # 광복절
    "2025-09-29",  # 입사자 없음
    "2025-10-03",  # 개천절
    "2025-10-06",  # 추석
    "2025-10-07",  # 추석연휴
    "2025-10-08",  # 대체공휴일
    "2025-10-09",  # 한글날
    "2025-12-25",  # 크리스마스
}

# 📆 오늘 날짜 가져오기
today = datetime.date.today().strftime("%Y-%m-%d")

# 🚫 오늘이 공휴일이면 실행하지 않고 종료
if today in HOLIDAYS:
    print(f"📢 오늘({today})은 공휴일이므로 실행하지 않습니다.")
    sys.exit(0)

# 환경 변수에서 Slack 토큰 로드
load_dotenv()
SLACK_TOKEN = os.environ.get("SLACK_TOKEN")

def send_slack_message(message, channel):
    try:
        client = WebClient(token=SLACK_TOKEN)
        client.chat_postMessage(channel=channel, text=message)
    except SlackApiError as e:
        print(f"⚠️ Error sending message to {channel} : {e}")

def main():
    for cluster in clusters:
        # 메시지 제목 설정
        header = f"*[공지｜클러스터 주차등록 및 이용 안내]*\n\n\n"

        notice_msg = (
            f"1. *중요도* : 중\n"
            f"2. *대상* : 평택 클러스터 임직원 전체\n"
            f"3. *주요 내용*\n\n"
            f"\n"
            f"안녕하세요? 평택 클러스터 구성원 여러분!\n\n"
            f"올바른 주차장 이용과 신규 주차 등록을 위해 공지 드리오니\n"
            f"아래 내용 참고하시어, 이용 부탁드리겠습니다.\n\n"
            f"\n"
            f":k체크: 주차 등록 시 *첨부자료* 참고하여 설문조사 후 *2층 인사총무팀에서 주차증* 수령\n"
            f"(설문조사 내 본인차량 *자동차등록증* 준비 및 *증빙자료* 첨부 必)\n\n"
            f"\n"
            f":k체크: *8층 주차장 외* 주차 확인 될 경우 *주차 위반 스티커 부착* 등 조치 예정\n"
            f":arrow_forward: 주차장 주차라인 내 주차 준수 / 경차 및 전기차 전용 준수\n"
            f":arrow_forward: 외부 불법 주/정차 수시 단속 진행 중_관공서\n"
            f":arrow_forward: 부속동(직원식당) 주차장 주차불가, 주차위반 스티커 또는 견인 조치 예정\n\n"
            f"\n"
            f"*:k체크: <https://docs.google.com/forms/d/e/1FAIpQLSfK121pYkYfmsL9I9MGX5tgA8Y6u1v03ZOP2RX9stmaLGH_Sg/viewform|주차등록링크>* *(Click)*\n\n"
            f"\n"
            f"*:slack: 문의사항 : 인사총무팀 총무/시설 담당자*\n\n"
            f"감사합니다.\n"
        )
 
        # 메시지 본문
        body = header + notice_msg

        # 슬랙 채널에 전송
        send_slack_message(body, cluster.channel)

if __name__ == "__main__":
    main()
