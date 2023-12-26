from package.PortfolioRebalancingCore import *
from package.PortfolioRebalancingCheck import check_ordered_qty, check_portfolio_mkt_qty
from package.PortfolioRebalancingPrint import get_account_info_and_show_briefing
from package.PortfolioRebalancingPrint import show_dashboard
from package.PortfolioCalculatorCore import estimate_original
from package.PortfolioCalculatorCore import estimate_adjusted_2
from pytz import timezone
import datetime
import json


PF_CODE = 'ki'  # './output/portfolio_output_{PF_CODE}'


def main():
    try:
        check_token_expired()  # KIS Developers는 초당 20건 API 호출 가능 ('API 호출 유량 안내' 2023.6.23 참조)

        # ---------------------------------------------------------------------------------------

        """[입력] 보유종목, 현재보유수량 등을 기록한 (output 폴더 안의) .json 파일을 불러옴"""
        with open(f'./output/portfolio_output_{PF_CODE}.json', 'r', encoding='UTF-8') as f:
            portfolio_output = json.load(f)
        real_time_cash, _ = get_account_info_and_show_briefing()
        portfolio_dict = portfolio_output[f'portfolio_dict_{PF_CODE}']
        # buyable_cash_dollar = float(portfolio_output[f'buyable_cash_dollar_{PF_CODE}'])  # 선택1) 기록지에 저장된 주문가능금액(테스트용)
        buyable_cash_dollar, _ = get_buyable_cash_dollar_and_exchange_rate()  # 선택2) 한투API로 가져온 실시간 주문가능금액

        # ---------------------------------------------------------------------------------------

        """[필터1] .json이 이번 달 자료가 아니면, 거부"""
        update_date_str = portfolio_output[f'update_date_{PF_CODE}']
        update_date = datetime.datetime.strptime(update_date_str, '%Y-%m-%d %H:%M:%S')
        current_date = datetime.datetime.now()
        is_same_month = (update_date.year, update_date.month) == (current_date.year, current_date.month)
        if not is_same_month:
            raise Exception('경고! 이번 달 자료가 아닙니다. 현재배분율, 목표배분율이 오래되어 잘못된 거래를 할 위험이 있어 종료합니다.')

        """[필터2] .json의 당일주문수량(주문한 날에 한정) 또는 현재보유수량 등이 실시간 정보와 불일치하면, 거부"""
        portfolio_ordered_qty_dict_proto = check_ordered_qty(**portfolio_dict)
        # if not은 None, {} 둘 다 체크함 (cf. 0, 0.0, ''. False 등도 판정함)
        if not portfolio_ordered_qty_dict_proto:  # 당일주문내역이 없는 경우(당일주문이 들어간 날은 재주문 안할 것이기에, 딱히 예외처리 안함)
            portfolio_mkt_is_ok, portfolio_crnt_qty_is_ok, portfolio_tkr_is_not_found = check_portfolio_mkt_qty(**portfolio_dict)
            if not portfolio_mkt_is_ok:
                raise Exception('경고! 시장분류가 맞지 않습니다. 착오로 잘못된 거래를 할 위험이 있어 종료합니다.')
            elif not portfolio_crnt_qty_is_ok:
                raise Exception('경고! 현재보유수량이 맞지 않습니다. 착오로 잘못된 거래를 할 위험이 있어 종료합니다.')
            elif portfolio_tkr_is_not_found:
                raise Exception('경고! 기록지(.json)에 누락된 종목이 있습니다. 착오로 잘못된 거래를 할 위험이 있어 종료합니다.')
            else:
                print('***** 종목누락, 시장분류, 현재보유수량 검사 이상없음 *****')

        # ---------------------------------------------------------------------------------------

        """[계산] 주문가능현금(buyable_cash_dollar : get_.._show_briefing 내부), 현재가(current_price: est_original 내부)는 API에서 최신으로 다운받아 사용함"""
        print()
        to_real_trade = True
        total_etfs_dollar, to_order_etfs_dollar, portfolio_dict = estimate_original(buyable_cash_dollar, **portfolio_dict)
        print('estimate_original)', end=' ')
        show_dashboard(total_etfs_dollar, buyable_cash_dollar, to_order_etfs_dollar, to_real_trade, **portfolio_dict)
        total_etfs_dollar, to_order_etfs_dollar, portfolio_dict = estimate_adjusted_2(total_etfs_dollar, buyable_cash_dollar, **portfolio_dict)
        print('estimate_adjusted)', end=' ')
        show_dashboard(total_etfs_dollar, buyable_cash_dollar, to_order_etfs_dollar, to_real_trade, **portfolio_dict)

        # ---------------------------------------------------------------------------------------

        # 썸머타임X) [매수]09:35(Korea 23:35), [조회] 13:00(Korea 03:00)
        # 썸머타임O) [매수]10:35(Korea 23:35), [조회] 14:00(Korea 03:00)
        t_now = datetime.datetime.now(timezone('America/New_York'))  # 현지시각 (뉴욕 기준)
        t_start = t_now.replace(hour=9, minute=35, second=0, microsecond=0)
        t_lunch = t_now.replace(hour=12, minute=00, second=0, microsecond=0)
        t_close = t_now.replace(hour=15, minute=50, second=0, microsecond=0)
        today = t_now.weekday()
        """공휴일(휴장일) 프로그램 종료도 추가 요망"""
        if today == 5 or today == 6:  # 토요일이나 일요일 (X)
            send_message('주말이므로 프로그램을 종료합니다.')
        elif t_now < t_start or t_close < t_now:  # ~ 09:35 or 15:50 ~ (X)
            send_message('평일이지만 정규장이 아니므로 프로그램을 종료합니다.')
        elif t_start < t_now < t_lunch:  # 09:35 ~ 12:00 (Order)
            time.sleep(1)
            send_message('[주문 시작]')
            launch_order(**portfolio_dict)
            send_message('[주문 완료]')
        elif t_lunch < t_now < t_close:  # 12:00 ~ 15:50 (Check)
            send_message('시황을 체크합니다. 로그를 확인 바랍니다.')
            print("오늘의 주문종목(전체) : {'(주문종목)': [(주문수량), (체결수량), (미체결수량), (매수매도여부)]}")
            today_order_dict = get_inquire_ccnl()
            print(today_order_dict)
            today_pending_order_dict = get_inquire_nccs()
            print(today_pending_order_dict, end=' ')
            print('-> 미체결종목\n')

        # ---------------------------------------------------------------------------------------

        """[출력] (시장분류, 현재보유량 일치여부 체크) 트레이딩 직전 정보로 기록 갱신"""
        if not portfolio_ordered_qty_dict_proto:
            portfolio_output = {
                f'update_date_{PF_CODE}': current_date.strftime('%Y-%m-%d %H:%M:%S'),
                f'buyable_cash_dollar_{PF_CODE}': buyable_cash_dollar,
                f'portfolio_dict_{PF_CODE}': portfolio_dict
            }
            with open(f'./output/portfolio_output_{PF_CODE}.json', 'w', encoding='UTF-8') as f:
                json.dump(portfolio_output, f, indent=2, sort_keys=False)
            print(f"portfolio_output_{PF_CODE}.json에 결과지를 남겼습니다 : {update_date} -> {current_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
        else:
            print('당일 주문으로 현재보유량이 바뀌었기 때문에 .json 파일을 갱신하지 않겠습니다.')

        """[이후] 포트폴리오의 이번 달 분량의 체결이 확정되면, *dashboard를 최신화(현재보유량 갱신)"""

    except Exception as e:
        send_message(f'[오류 발생]{e}')


main()
