import os
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ==============================================================================
# [설정]
# ==============================================================================
USER_ID = os.environ.get("USER_ID")
USER_PW = os.environ.get("USER_PW")
TARGET_URL = "https://group.kurlycorp.kr/gw/uat/uia/egovLoginUsr.do"

DEPARTMENT = "평택"                      # 검색할 부서 (진단은 1개만)
DOC_CATEGORIES = ["구매요청서", "발주승인요청서", "사전 품의서"]
MAX_DOCS_PER_CATEGORY = 2                # 양식별로 열어볼 문서 수
KEYWORDS = ["금액", "합계", "총액", "공급가액", "VAT", "부가세", "단가", "수량"]

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_out")
os.makedirs(OUT_DIR, exist_ok=True)


# ==============================================================================
# [도구]
# ==============================================================================
def save_text(filename, content):
    with open(os.path.join(OUT_DIR, filename), "w", encoding="utf-8") as f:
        f.write(content)


def dump_current(driver, prefix, texts, depth=0):
    """현재 프레임의 HTML/텍스트를 저장하고, 하위 iframe도 재귀적으로 저장"""
    try:
        save_text(prefix + ".html", driver.page_source)
    except Exception as e:
        print(f"    HTML 저장 실패({prefix}): {e}")
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text
    except Exception:
        body_text = ""
    texts.append((prefix, body_text))

    if depth >= 3:
        return
    try:
        frame_count = len(driver.find_elements(By.CSS_SELECTOR, "iframe, frame"))
    except Exception:
        frame_count = 0

    for i in range(frame_count):
        try:
            frames = driver.find_elements(By.CSS_SELECTOR, "iframe, frame")
            driver.switch_to.frame(frames[i])
            dump_current(driver, f"{prefix}_f{i}", texts, depth + 1)
            driver.switch_to.parent_frame()
        except Exception as e:
            print(f"    프레임 {i} 처리 실패: {e}")
            try:
                driver.switch_to.parent_frame()
            except Exception:
                pass


def extract_keyword_lines(texts):
    lines = []
    for prefix, text in texts:
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if any(k in line for k in KEYWORDS) and re.search(r"\d", line):
                lines.append(f"[{prefix}] {line}")
    return lines


def enter_content_frame(driver):
    try:
        driver.switch_to.frame("_content")
    except Exception:
        driver.switch_to.frame(0)


# ==============================================================================
# [메인]
# ==============================================================================
def run():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)
    summary = []

    try:
        print("1. 로그인...")
        driver.get(TARGET_URL)
        time.sleep(2)
        driver.find_element(By.ID, "userId").send_keys(USER_ID)
        driver.find_element(By.ID, "userPw").send_keys(USER_PW)
        driver.find_element(By.ID, "userPw").send_keys(Keys.RETURN)
        time.sleep(5)

        main_window = driver.current_window_handle
        for h in driver.window_handles:
            if h != main_window:
                driver.switch_to.window(h)
                driver.close()
        driver.switch_to.window(main_window)

        print("2. 수신참조함 이동...")
        elec = wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'전자결재')]")))
        driver.execute_script("arguments[0].click();", elec)
        time.sleep(2)
        inbox = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(),'수신참조함')]")))
        driver.execute_script("arguments[0].click();", inbox)
        time.sleep(3)

        enter_content_frame(driver)
        time.sleep(2)

        try:
            Select(driver.find_element(By.TAG_NAME, "select")).select_by_visible_text("전체")
        except Exception:
            pass

        for category in DOC_CATEGORIES:
            print(f"=== 양식: {category} ===")
            try:
                doc_input = driver.find_element(By.ID, "txtDocTp")
                driver.execute_script("arguments[0].value = arguments[1];", doc_input, category)
                dept_input = driver.find_element(By.ID, "txtDeptNm")
                driver.execute_script("arguments[0].value = arguments[1];", dept_input, DEPARTMENT)
                try:
                    btn = driver.find_element(
                        By.XPATH,
                        "//input[@value='검색'] | //button[contains(text(),'검색')] | //a[contains(text(),'검색')]",
                    )
                    driver.execute_script("arguments[0].click();", btn)
                except Exception:
                    dept_input.send_keys(Keys.RETURN)
                time.sleep(3)
            except Exception as e:
                print(f"  검색 실패: {e}")
                continue

            # 상태와 상관없이 위에서부터 N건
            targets = []
            rows = driver.find_elements(By.TAG_NAME, "tr")
            for i, row in enumerate(rows):
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) < 12 or "기안일자" in row.text:
                    continue
                title = driver.execute_script("return arguments[0].textContent;", cols[3]).strip()
                if len(title) < 2:
                    continue
                targets.append((i, title))
                if len(targets) >= MAX_DOCS_PER_CATEGORY:
                    break

            print(f"  열어볼 문서 {len(targets)}건")

            for n, (row_index, title) in enumerate(targets, start=1):
                tag = f"{category.replace(' ', '')}_{n}"
                try:
                    current_rows = driver.find_elements(By.TAG_NAME, "tr")
                    cell = current_rows[row_index].find_elements(By.TAG_NAME, "td")[3]
                    handles_before = driver.window_handles

                    links = cell.find_elements(By.TAG_NAME, "a")
                    driver.execute_script("arguments[0].click();", links[0] if links else cell)

                    WebDriverWait(driver, 8).until(lambda d: len(d.window_handles) > len(handles_before))
                    new_window = [h for h in driver.window_handles if h not in handles_before][0]
                    driver.switch_to.window(new_window)
                    time.sleep(4)  # 문서 본문 로딩 대기

                    texts = []
                    dump_current(driver, tag, texts)
                    driver.switch_to.default_content()

                    kw_lines = extract_keyword_lines(texts)
                    summary.append(f"##### {tag} | 제목: {title} | URL: {driver.current_url}")
                    summary.extend(kw_lines if kw_lines else ["(금액 관련 줄을 찾지 못함)"])
                    summary.append("")
                    print(f"  {tag}: 키워드 줄 {len(kw_lines)}개")

                    driver.close()
                    driver.switch_to.window(main_window)
                    enter_content_frame(driver)
                    time.sleep(1)

                except Exception as e:
                    print(f"  문서 처리 실패({tag}): {e}")
                    summary.append(f"##### {tag} 처리 실패: {e}\n")
                    try:
                        for h in driver.window_handles:
                            if h != main_window:
                                driver.switch_to.window(h)
                                driver.close()
                        driver.switch_to.window(main_window)
                        enter_content_frame(driver)
                    except Exception:
                        pass

    except Exception as e:
        print(f"에러 발생: {e}")
        summary.append(f"전체 에러: {e}")
    finally:
        save_text("summary.txt", "\n".join(summary))
        driver.quit()
        print("진단 완료 - debug_out/summary.txt 확인")


if __name__ == "__main__":
    run()
