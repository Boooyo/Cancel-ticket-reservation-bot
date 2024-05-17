from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import logging

# 로그 설정
logging.basicConfig(level=logging.INFO)

def log(message):
    logging.info(message)

def find_and_switch_to_frame(driver, frame_id):
    driver.switch_to.default_content()
    frame = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, frame_id)))
    driver.switch_to.frame(frame)

def handle_alert(driver):
    try:
        alert = driver.switch_to.alert
        alert.accept()
        time.sleep(3)
    except:
        pass

def select_seat(seat, cbCheck):
    seat_grade = seat['alt'][seat['alt'].find('[') + 1:]
    return (
        (seat_grade.find("VIP") != -1 and cbCheck[0] == 1) or
        (seat_grade.find("R") != -1 and cbCheck[1] == 1) or
        (seat_grade.find("S") != -1 and cbCheck[2] == 1) or
        (seat_grade.find("A") != -1 and cbCheck[3] == 1) or
        cbCheck[4] == 1
    )

def find_empty_seat(driver, cbCheck):
    while True:
        find_and_switch_to_frame(driver, 'ifrmSeatDetail')
        bs4 = BeautifulSoup(driver.page_source, "html.parser")
        seat_list = bs4.findAll('img', class_='stySeat')

        for seat in seat_list:
            if select_seat(seat, cbCheck):
                driver.execute_script(seat['onclick'] + ";")
                find_and_switch_to_frame(driver, 'ifrmSeat')
                driver.execute_script("javascript:fnSelect();")
                log("빈좌석 찾기 성공")
                time.sleep(0.5)
                return True

        handle_alert(driver)
        find_and_switch_to_frame(driver, 'ifrmSeatView')
        bs4 = BeautifulSoup(driver.page_source, "html.parser")
        area_list = bs4.findAll('area')

        for area in area_list:
            driver.execute_script(area["href"])
            time.sleep(0.5)
            handle_alert(driver)

        if not area_list:
            break

    return False

def select_ticket(driver, userTicket):
    find_and_switch_to_frame(driver, 'ifrmBookStep')
    bs4 = BeautifulSoup(driver.page_source, "html.parser")
    ticket_list = bs4.findAll('select')

    elem = next((ticket["index"] for ticket in ticket_list if userTicket in ticket["pricegradename"]), '01')

    try:
        driver.find_element(By.XPATH, f"//td[@class='taL']//select[@index='{elem}']//option[@value='1']").click()
    except:
        driver.find_element(By.XPATH, "//td[@class='taL']//select[@pricegrade='01']//option[@value='1']").click()

    driver.switch_to.default_content()
    driver.execute_script("javascript:fnNextStep('P');")
    handle_alert(driver)
    log("가격/할인 선택")
    time.sleep(0.5)

def confirm_order_info(driver, userNum):
    find_and_switch_to_frame(driver, 'ifrmBookStep')
    driver.find_element(By.XPATH, "//td[@class='form']//input[@id='YYMMDD']").send_keys(userNum)
    driver.switch_to.default_content()
    driver.execute_script("javascript:fnNextStep('P');")
    log("배송선택/주문자확인")
    time.sleep(0.5)

def select_payment(driver, userBank):
    find_and_switch_to_frame(driver, 'ifrmBookStep')
    driver.find_element(By.XPATH, "//tr[@id='Payment_22004']//input[@name='Payment']").click()
    driver.find_element(By.XPATH, f"//select[@id='BankCode']//option[@value='{userBank}']").click()
    driver.switch_to.default_content()
    driver.execute_script("javascript:fnNextStep('P');")
    log("결제하기")
    time.sleep(0.5)

def accept_terms(driver):
    find_and_switch_to_frame(driver, 'ifrmBookStep')
    driver.find_element(By.XPATH, "//input[@id='CancelAgree']").click()
    driver.find_element(By.XPATH, "//input[@id='CancelAgree2']").click()
    driver.switch_to.default_content()
    driver.execute_script("javascript:fnNextStep('P');")
    log("예매 완료")
    time.sleep(0.5)

def save_booking_info(driver):
    find_and_switch_to_frame(driver, 'ifrmBookEnd')
    result = open("result.txt", "w", encoding="utf-8")

    def write_info(title, element):
        text = driver.find_element(By.XPATH, element).text
        result.write(f"{title} : {text}\n")

    result.write("___________ 상품정보 ___________\n")
    write_info("예약 번호", "//p[@class='tit']//span[1]")
    write_info("상품", "//div[@class='contT']//table//tbody//tr[1]//th")
    write_info("장소", "//div[@class='contT']//table//tbody//tr[2]//th")
    write_info("일시", "//div[@class='contT']//table//tbody//tr[3]//th")
    write_info("좌석", "//div[@class='contT']//table//tbody//tr[4]//th")

    result.write("__________ 예매자 정보 __________\n")
    write_info("예매자", "//div[@class='contB']//table//tbody//tr[1]//th")
    write_info("예매자 연락처", "//div[@class='contB']//table//tbody//tr[2]//th")
    write_info("티켓수령방법", "//div[@class='contB']//table//tbody//tr[3]//th")

    result.write("___________ 결제정보 ___________\n")
    write_info("총 결제금액", "//table[@class='new_t']//thead//tr[1]//th")
    write_info("티켓금액", "//table[@class='new_t']//tbody//tr[1]//th")
    write_info("수수료", "//table[@class='new_t']//tbody//tr[2]//th")
    write_info("배송료", "//table[@class='new_t']//tbody//tr[3]//th")

    result.write("_________ 결제상세정보 _________\n")
    write_info("결제방법", "//div[@class='completeR']//table//tbody//tr[1]//th")
    write_info("입금마감일시", "//div[@class='completeR']//table//tbody//tr[2]//th")
    write_info("입금계좌", "//div[@class='completeR']//table//tbody//tr[3]//th")
    write_info("예금주명", "//div[@class='completeR']//table//tbody//tr[4]//th")

    result.close()
    log("예매 정보 출력")

def main(userTicket, userNum, userBank, cbCheck):
    driver = webdriver.Chrome()

    try:
        # 2단계 프레임 받아오기
        find_and_switch_to_frame(driver, 'ifrmSeat')

        # 미니맵 존재여부 검사
        try:
            find_and_switch_to_frame(driver, 'ifrmSeatView')
            bs4 = BeautifulSoup(driver.page_source, "html.parser")
            elem = bs4.find('map')
        except:
            elem = None

        # 빈 좌석 찾기
        if elem:
            area_list = bs4.findAll('area')
            for area in area_list:
                driver.execute_script(area["href"])
                if find_empty_seat(driver, cbCheck):
                    break
        else:
            find_empty_seat(driver, cbCheck)

        # 3단계 가격/할인 선택
        select_ticket(driver, userTicket)

        # 4단계 주문자 정보 확인
        confirm_order_info(driver, userNum)

        # 5-1단계 결제 수단 선택
        select_payment(driver, userBank)

        # 5-2단계 약관 동의
        accept_terms(driver)

        # 예매 정보 저장
        save_booking_info(driver)

        # 마이페이지 접속
        driver.switch_to.window(driver.window_handles[0])
        driver.find_element(By.XPATH, '//li[@class="mypage"]/a').click()
        log("마이페이지 접속")

        # 예매결과 확인
        driver.execute_script("javascript: fnPlayBookDetail(0);")
        log("예매결과 확인")

    except Exception as e:
        log(f"에러 발생: {str(e)}")
    finally:
        driver.close()
        log("예매창 닫기")

if __name__ == "__main__":
    userTicket = "티켓명"
    userNum = "주민번호 앞 6자리"
    userBank = "은행 코드"
    cbCheck = [1, 0, 0, 0, 1]  # 예시: VIP 좌석 또는 아무 좌석
    main(userTicket, userNum,
