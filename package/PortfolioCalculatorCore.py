from package.PortfolioRebalancingCore import *
from package.PortfolioRebalancingPrint import show_dashboard
import copy


def estimate_original(buyable_cash_dollar: float, **portfolio_dict):
    """목표매매수량을 계산할 때 (소수점을 버리고) 정수를 받아오는 전통적인 로직"""
    """보유종목 : [자산분류, 시장분류, 단가($), 현재보유량(주), 현재평가금액($), 현재배분율[R](%), (현재배분율[I](%)), 목표보유량(주), 목표평가금액($),
                목표배분율[R](%), (목표배분율[I](%)), 목표매매량(주), 예상매매금액($), 괴리율(%), 매수1호가($), 매도1호가($)]"""

    realtime_total_etfs_dollar = 0.00
    for ticker, list in portfolio_dict.items():
        market = list[1]
        current_qty = list[3]
        current_price = get_current_price(ticker, market)
        bid_price, ask_price = get_bid_ask_price(ticker, market)
        list[2] = current_price
        list[4] = current_price * current_qty
        list[14] = bid_price
        list[15] = ask_price
        # 실시간으로 업데이트된 현재가를 반영한 현재 보유주식의 총합 (정교한 잔액 파악으로 계산오차를 줄이기 위함)
        realtime_total_etfs_dollar += list[4]
    """etfs_cash_sum > 0이 아니면, 오류 발생"""
    etfs_cash_sum = realtime_total_etfs_dollar + buyable_cash_dollar

    to_order_etfs_dollar = 0.00
    for ticker, list in portfolio_dict.items():
        current_price = list[2]
        current_qty = list[3]
        target_percentage = list[10] / 100
        target_qty = int((etfs_cash_sum * target_percentage) // current_price)
        # '괴리율' : 목표배분율(이상값) - 목표배분율(실제값)
        disparate_rate = (current_price * target_qty - etfs_cash_sum * target_percentage) / etfs_cash_sum * 100
        list[5] = (current_price * current_qty / etfs_cash_sum) * 100
        list[7] = target_qty
        list[8] = current_price * target_qty
        list[9] = current_price * target_qty / etfs_cash_sum * 100
        list[11] = target_qty - current_qty
        list[12] = current_price * (target_qty - current_qty)
        list[13] = round(disparate_rate, 4)
        to_order_etfs_dollar += list[12]

    return realtime_total_etfs_dollar, to_order_etfs_dollar, portfolio_dict


def assist_adjusted_1(total_etfs_dollar: float, buyable_cash_dollar: float, to_show_dashboard: bool, **portfolio_dict):
    exclusion_etfs_dollar = 0.00  # **현재 열외할 자산금액의 합계 (주문 가능 현금 : buyable_cash_dollar로 배분해야 함)**
    exclusion_current_percentage = 0.00
    exclusion_target_percentage = 0.00
    to_order_etfs_dollar = 0.00  # 앞으로 매수할 자산금액의 합계
    portfolio_dict_adj = {}  # '매수할 종목'만으로 리밸런싱하고자, 목표배분율을 초과하는 자산은 열외

    for ticker, list in portfolio_dict.items():
        if list[11] >= 0:
            portfolio_dict_adj[ticker] = copy.deepcopy(portfolio_dict[ticker])  # 깊은복사(테이블 새로만들기)
        else:
            exclusion_etfs_dollar += list[4]
            exclusion_current_percentage += list[6]
            exclusion_target_percentage += list[10]
    """(100 - exclusion_OOOOOO_percentage) > 0, etfs_cash_sum_adj > 0이 아니면, 오류 발생"""
    total_etfs_dollar_adj = total_etfs_dollar - exclusion_etfs_dollar
    etfs_cash_sum_adj = total_etfs_dollar_adj + buyable_cash_dollar

    for ticker, list in portfolio_dict_adj.items():
        list[5] = list[4] / total_etfs_dollar_adj * 100 if total_etfs_dollar_adj != 0 else 0
        list[6] = list[6] / (100 - exclusion_current_percentage) * 100
        list[10] = list[10] / (100 - exclusion_target_percentage) * 100
        list[7] = int(etfs_cash_sum_adj * (list[10] / 100) // list[2])
        list[8] = list[2] * list[7]
        list[9] = list[8] / etfs_cash_sum_adj * 100
        list[11] = list[7] - list[3]
        list[12] = list[2] * list[11]
        list[13] = round((list[8] - etfs_cash_sum_adj * (list[10] / 100)) / etfs_cash_sum_adj * 100, 4)
        to_order_etfs_dollar += list[12]

    if to_show_dashboard:
        show_dashboard(total_etfs_dollar_adj, buyable_cash_dollar, to_order_etfs_dollar, False, **portfolio_dict_adj)

    return total_etfs_dollar_adj, to_order_etfs_dollar, portfolio_dict_adj


def estimate_adjusted_1(total_etfs_dollar: float, buyable_cash_dollar: float, to_show_dashboard: bool, **portfolio_dict):
    """(선택사항) buy-only로 만드는 로직"""
    total_etfs_dollar_adj = total_etfs_dollar
    portfolio_dict_adj = portfolio_dict

    while True:
        """(매수only 로직을 만들고자) 목표배분율을 초과하는 종목의 목록을 반복문을 돌려서 걸러질 때까지 필터링하고 계산함"""
        until_no_more_etf_to_sell = True
        total_etfs_dollar_adj, to_order_etfs_dollar, portfolio_dict_adj = assist_adjusted_1(total_etfs_dollar_adj, buyable_cash_dollar,
                                                                                            to_show_dashboard, **portfolio_dict_adj)
        for ticker, list in portfolio_dict_adj.items():
            if list[11] < 0:
                until_no_more_etf_to_sell = False
                break
            else:
                continue
        if until_no_more_etf_to_sell == True:
            break

    portfolio_buy_qty_dict = {}
    for ticker in portfolio_dict:
        portfolio_buy_qty_dict[ticker] = 0
    for ticker, list in portfolio_dict_adj.items():
        if list[11] > 0:
            portfolio_buy_qty_dict[ticker] = list[11]

    """etfs_cash_sum > 0이 아니면, 오류 발생"""
    etfs_cash_sum = total_etfs_dollar + buyable_cash_dollar
    to_order_etfs_dollar = 0.00
    for ticker, list in portfolio_dict.items():
        """위에서 구한 목표매매량응 다시 원래있던 전체 목록에 적용하고 새로운 목표배분율을 구함 """
        current_price = list[2]
        current_qty = list[3]
        target_percentage = list[10] / 100
        target_qty = list[3] + portfolio_buy_qty_dict[ticker]
        disparate_rate = (current_price * target_qty - etfs_cash_sum * target_percentage) / etfs_cash_sum * 100
        list[7] = target_qty
        list[8] = current_price * target_qty
        list[9] = current_price * target_qty / etfs_cash_sum * 100
        list[11] = target_qty - current_qty
        list[12] = current_price * (target_qty - current_qty)
        list[13] = round(disparate_rate, 4)
        to_order_etfs_dollar += list[12]

    return total_etfs_dollar, to_order_etfs_dollar, portfolio_dict


def estimate_adjusted_2(total_etfs_dollar: float, buyable_cash_dollar: float, **portfolio_dict):
    """잔돈으로 마저 사들이는 로직 (아래 계산식은 구매가와 거래수수료를 반영하여 차감)"""
    to_order_etfs_dollar = 0.00
    for ticker, list in portfolio_dict.items():
        to_order_etfs_dollar += list[12]
    remained_balance = buyable_cash_dollar - to_order_etfs_dollar
    """etfs_cash_sum > 0이 아니면, 오류 발생"""
    etfs_cash_sum = total_etfs_dollar + buyable_cash_dollar

    sell_amount_abs = 0
    for ticker, list in portfolio_dict.items():
        if list[12] < 0:
            sell_amount_abs += abs(list[12])
    print('Buy-only는 해당사항 없음, 매도 시 주문가능금액 차감액수 계산(전체 매도금액의 1.068% ~ 1.215% 가량 제외됨)')
    print('{0:.3f} - {1:.3f}(매도금액의 1.5%) = {2:.3f}'.format(remained_balance, sell_amount_abs * 1.5 / 100,
                                                           remained_balance - (sell_amount_abs * 1.5 / 100)))
    remained_balance -= sell_amount_abs * 1.5 / 100

    buy_amount_abs = 0
    for ticker, list in portfolio_dict.items():
        if list[12] > 0:
            buy_amount_abs += list[12]
    print('매수 시 주문가능금액 차감액수 계산(기본 거래수수료인 전체 매수금액의 0.25%로 가정)')
    print('{0:.3f} - {1:.3f}(매수금액의 0.25%) = {2:.3f}'.format(remained_balance, buy_amount_abs * 0.25 / 100,
                                                            remained_balance - (buy_amount_abs * 0.25 / 100)))
    remained_balance -= buy_amount_abs * 0.25 / 100

    print('>> 이미 위의 계산표대로 주문하고 난 후, 낱개주문한다고 가정 (즉, 수수료 계산이 보수적임)\n')
    while True:
        """잔액이 고갈될 때까지 추가주문하는 계산식 (단, '주문금액 = n%상향매수 * 거래수수료 * 현재가' 임을 감안함)"""
        """+1주 했을 경우의 각각의 예상 괴리율(%)을 리스트에 넣고 max sort"""
        """선정된 최우선순위의 주식 +1주"""
        portfolio_disparate_rate_dict: dict[str, float] = {}
        for ticker, list in portfolio_dict.items():
            portfolio_disparate_rate_dict[ticker] = 100.00

        for ticker, list in portfolio_dict.items():
            # (1)남아있는 잔액보다 단가가 비싸거나, (2)목표배분율이 0%인 종목은 추가주문대상에서 제외
            if remained_balance < list[2] * (1 + LIMITED_ORDER_DISADVANTAGE_RATE_PCT / 100) * (1 + 0.25 / 100):
                continue
            elif list[10] == 0:
                continue
            else:
                evlu_real = list[2] * (list[7] + 1)  # 1주를 더 살 경우 해당 종목의 목표평가금액[현실값] (ex. $99.80 * 20주 + $99.80 * 1주)
                evlu_ideal = etfs_cash_sum * (list[10] / 100)  # 해당 종목의 목표평가금액[이상값] (ex. $10000.00 * 20%)
                evlu_disparate_rate = (evlu_real - evlu_ideal) / etfs_cash_sum * 100  # 해당 주식의 괴리율 계산
                portfolio_disparate_rate_dict[ticker] = evlu_disparate_rate
        # noinspection PyTypeChecker
        portfolio_disparate_rate_dict = dict(sorted(portfolio_disparate_rate_dict.items(), key=lambda x: x[1], reverse=False))
        ticker_to_add = min(portfolio_disparate_rate_dict, key=portfolio_disparate_rate_dict.get)

        for ticker, value in portfolio_disparate_rate_dict.items():
            if value != 100.00:
                print(f"'{ticker}': {value:.4f}", end=' ')
            # else:
            #     print(f"'{ticker}': {value:.2f}", end=' ')

        if portfolio_disparate_rate_dict[ticker_to_add] == 100.00:
            print('FINISHED\n')
            break
        else:
            print(f'\n {ticker_to_add:<4} (+1)', end=' ')

        ticker_to_add_list = portfolio_dict[ticker_to_add]
        ticker_to_add_list[7] = ticker_to_add_list[7] + 1
        ticker_to_add_list[8] = ticker_to_add_list[2] * ticker_to_add_list[7]
        # ticker_to_add_list[9](목표배분율[R])은 cash의 비율을 가져오는 것이므로, 다른 주식의 목표배분율에 영향을 주지 않음
        ticker_to_add_list[9] = ticker_to_add_list[8] / etfs_cash_sum * 100
        ticker_to_add_list[11] = ticker_to_add_list[11] + 1
        ticker_to_add_list[12] = ticker_to_add_list[2] * ticker_to_add_list[11]
        ticker_to_add_list[13] = (ticker_to_add_list[8] - etfs_cash_sum * (ticker_to_add_list[10] / 100)) / etfs_cash_sum * 100
        to_order_etfs_dollar += ticker_to_add_list[2]
        remained_balance -= ticker_to_add_list[2] * (1 + LIMITED_ORDER_DISADVANTAGE_RATE_PCT / 100) * (1 + 0.25 / 100)
        print('    // ', end='')
        print(f'{1 + LIMITED_ORDER_DISADVANTAGE_RATE_PCT / 100:.4f} * {1 + 0.25 / 100:.4f} * ${ticker_to_add_list[2]}'
              f'({LIMITED_ORDER_DISADVANTAGE_RATE_PCT}%상향매수 * 0.25%거래수수료(가정) * 현재가)로 낱개구매 후 예상잔액 :'
              f'${remained_balance:.2f}\n')

    return total_etfs_dollar, to_order_etfs_dollar, portfolio_dict
