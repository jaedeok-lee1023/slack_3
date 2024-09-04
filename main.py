import os

import arrow
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from kurly import clusters

# 환경 변수에서 Slack 토큰, 채널을 로드
load_dotenv()
SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
def send_slack_message(message, channel):
    try:
        client = WebClient(token=SLACK_TOKEN)
        client.chat_postMessage(channel=channel, text=message)
    except SlackApiError as e:
        print(f"Error sending message to {channel} : {e}")
def main():
    for cluster in clusters:
        # 메시지 제목 설정
        header = f":loudspeaker: *『인사총무팀 공지』* <!channel>\n\n"

        notice_msg = (
            f"안녕하세요? 평택 클러스터 구성원 여러분\n\n올바른 주차등록과 주차장 이용을 위해 구성원 여러분들께 다음과 같이 공지 드리오니 꼭 협조 부탁드리겠습니다.\n\n"
            f"\n"
            f"\n"
            f":k체크: 주차 등록 시 *스레드 링크*를 통한 설문조사 후 *2층 통합사무실에서 주차증* 수령\n(설문조사 내 본인차량 *자동차등록증* 준비 및 *증빙자료* 첨부 必\n\n"
            f"\n"
            f":k체크: *8층 주차장 외* 주차 확인 될 경우 *주차 위반 스티커 부착* 등 조치 예정\n"
            f":arrow_forward: 주차장 주차라인 내 주차 준수 / 경차 및 전기차 전용 준수\n"
            f":arrow_forward: 지자체에서 외부 불법 주/정차 수시 단속 중\n"
            f":arrow_forward: 부속동 주차장 이용 시 직원식당 측에서 견인 등 조치 예정\n\n"
            f"\n"
            f"\n"
            f"*자세한 자료는 스레드 참고 바랍니다!*\n\n"
            f"*문의사항 : 인사총무팀 총무/시설 담당자*\n\n"
            f"감사합니다.\n"
        )
 
        # 메시지 본문
        body = header + notice_msg

        # 슬랙 채널에 전송
        send_slack_message(body, cluster.channel)

if __name__ == "__main__":
    main()
