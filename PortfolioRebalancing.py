from package.PortfolioAboutDashboard import get_account_info_and_show_briefing
from package.PortfolioCalculatorCore import distribute_buyable_cash, estimate_print_portfolio
from package.PortfolioRebalancingCore import check_token_expired, send_message, launch_order, get_inquire_ccnl_order, \
    get_inquire_ccnl_order_details
from package.PortfolioRebalancingCheck import check_backup_file_created_within_twenty_for_hours, check_portfolio_mkt_qty, \
    convert_to_portfolio_mkt_qty_dict, show_ccnl_nccs_concisely
from pytz import timezone
import datetime
import json
import time


"""주의 : TEST_MODE, PF_BUY_ONLY_LIST는 모두 실제 거래에 영향을 끼칠 수 있으므로, '취급주의'할 것!"""
# default : False, [1, 2], [1, 1, 1]
TEST_MODE = False
PF_BUY_ONLY_LIST = [1, 2]  # (중요) 현재 기준 마지막 포트폴리오(3)만 매도+매수 모드, 나머지(1, 2)는 매수 모드
FUND_RATIO = [1, 1, 1]


def main():
    try:
        check_token_expired()  # KIS Developers는 초당 20건 API 호출 가능 ('API 호출 유량 안내' 2023.6.23 참조)
        t_now = datetime.datetime.now(timezone('America/New_York'))
        t_start = t_now.replace(hour=9, minute=35, second=0, microsecond=0)
        t_lunch = t_now.replace(hour=12, minute=00, second=0, microsecond=0)
        t_close = t_now.replace(hour=15, minute=50, second=0, microsecond=0)
        today = t_now.weekday()

        # ---------------------------------------------------------------------------------------

        """[입력] 1) 실시간 잔고를 api로 읽고 buyable_cash_dollar_sum 불러옴  2) 포트폴리오 정보를 기록한 .json 파일에서 portfolio_dict 불러옴"""
        """[필터1] 'backup-portfolio-mkt-qty-info.json, portfolio_output_n.json 파일'이 24시간 이내의 자료인지 검사"""
        buyable_cash_dollar_sum, _, _ = get_account_info_and_show_briefing()
        portfolio_outputs = []
        portfolio_dicts = []
        with open(f'./config/backup-portfolio-mkt-qty-info.json', 'r', encoding='UTF-8') as f:
            backup_portfolio_mkt_qty_info = json.load(f)
        check_backup_file_created_within_twenty_for_hours([backup_portfolio_mkt_qty_info])
        pf_count = len(backup_portfolio_mkt_qty_info['portfolio_mkt_qty_dict'])
        for i in range(pf_count):
            with open(f'./output/portfolio_output_{i + 1}.json', 'r', encoding='UTF-8') as pof:
                portfolio_outputs.append(json.load(pof))
            portfolio_dicts.append(portfolio_outputs[i][f'portfolio_dict_{i + 1}'])
        check_backup_file_created_within_twenty_for_hours(portfolio_outputs)

        """[필터2] 'portfolio_output_n.json 파일 <-> api 실시간 정보'의 시장분류(mkt)와 현재보유수량(qty) 동기화 여부 검사"""
        """주의 : 포트폴리오 내/간 종목의 중복/누락 검사는 PortfolioCalculator.py에서 이미 했음을 가정, ~output_n.json 파일을 임의로 조작하지 말 것"""
        today_order_dict = get_inquire_ccnl_order(False)
        if not today_order_dict:  # 리밸런싱 전에 당일주문 이미 했는지 여부 확인
            check_portfolio_mkt_qty(portfolio_dicts)

        """************************************************************"""
        """[필터3] 주문시간이 아닌 경우, 아래와 같은 메시지를 남기고 종료"""
        if not TEST_MODE:
            if today == 5 or today == 6:  # 토요일이나 일요일 (X)
                send_message('주말이므로 프로그램을 종료합니다.')
                return
            elif t_now < t_start or t_close < t_now:  # ~ 09:35 or 15:50 ~ (X)
                send_message('평일이지만 정규장이 아니므로 프로그램을 종료합니다.')
                return
            elif t_lunch < t_now < t_close:  # 12:00 ~ 15:50 (Check)
                send_message('당일 주문/체결 내역, 그리고 슬리피지를 확인합니다.')
                show_ccnl_nccs_concisely(today_order_dict, portfolio_dicts)
                get_inquire_ccnl_order_details(True, len(FUND_RATIO))
                return
            else:  # 09:35 ~ 12:00 (Order)
                pass
        """************************************************************"""

        # ---------------------------------------------------------------------------------------

        """[계산준비] 리밸런싱을 위한 (각 포트폴리오의) 구매가능현금 배분금액을 정함"""
        print()
        mkt_qty_dict = convert_to_portfolio_mkt_qty_dict(portfolio_dicts)
        buyable_cash_dollar_sum, buyable_cash_dollar_list = distribute_buyable_cash(buyable_cash_dollar_sum, mkt_qty_dict, FUND_RATIO)
        expected_remaining_cash_dollar_list = []
        print()

        for j in range(pf_count - 1, -1, -1):  # 2, 1, 0
            time.sleep(1)  # API call 관리
            """[계산] 불러온 포트폴리오 정보(qtys of cash, assets)를 토대로 구매할 수량을 계산함"""
            """주의 : est_print_portfolio() 안에서 current price, bid_ask_price를 for문으로 API 호출함 (안전 : 호출 20건 당 1초 초과)"""
            buy_only_mode = True if j + 1 in PF_BUY_ONLY_LIST else False
            buyable_cash_dollar = buyable_cash_dollar_list[j]
            portfolio_dict = portfolio_dicts[j]
            remaining_cash_dollar = estimate_print_portfolio(buy_only_mode, str(j + 1), buyable_cash_dollar, portfolio_dict)
            expected_remaining_cash_dollar_list.insert(0, round(remaining_cash_dollar, 4))

            """[주문] 위에서 구매수량을 계산한 직후 '즉시' 주문함"""
            """주의 : launch_order() 안에서 current_price를 for문으로 API 호출함 (안전 : 한 포트폴리오 당 20종목 이상을 매매하지 않는 선에서 관리)"""
            """주의 : launch_order()는 실제 거래가 진행되므로, '취급주의'할 것!"""
            # SummerTimeX) [Order]09:35(Korea 23:35), [Check] 14:00(Korea 04:00)
            # SummerTimeO) [Order]10:35(Korea 23:35), [Check] 15:00(Korea 04:00)
            t_now = datetime.datetime.now(timezone('America/New_York'))
            what_time_is_it_now = t_now.strftime('%Y-%m-%d %H:%M:%S')
            """$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$"""
            if not TEST_MODE:
                send_message(f'현지 시각(뉴욕 기준): {what_time_is_it_now}')
                send_message(f'portfolio_{j + 1})')
                time.sleep(1)  # API call 관리
                send_message('[주문 시작]')
                launch_order(**portfolio_dicts[j])  # 주의! 실제 매매주문 작동함
                send_message('[주문 완료]')
            """$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$"""
            print('\n')

        # ---------------------------------------------------------------------------------------

        """************************************************************"""
        """[출력] (주문 완료에 한해) 주문 시점의 데이터로 기록 최신화"""
        if not TEST_MODE:
            for j in range(pf_count - 1, -1, -1):  # 2, 1, 0
                update_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                portfolio_output = {
                    f'update_date': update_date,
                    f'buyable_cash_dollar_{j + 1}': buyable_cash_dollar_list[j],
                    f'expected_remaining_cash_dollar_{j + 1}': expected_remaining_cash_dollar_list[j],
                    f'portfolio_dict_{j + 1}': portfolio_dicts[j]
                }
                with open(f'./output/portfolio_output_{j + 1}.json', 'w', encoding='UTF-8') as pof:
                    json.dump(portfolio_output, pof, indent=2, sort_keys=False)
                    print(f'Saved the portfolio calculation output in ./output/portfolio_output_{j + 1}.json.')
        else:
            print('The test mode has been completed.')
        """************************************************************"""

        """[이후] 포트폴리오의 이번 달 분량 체결이 확정되면, *dashboard를 최신화"""

    except Exception as e:
        send_message(f'[오류 발생]{e}')


main()
