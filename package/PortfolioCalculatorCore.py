from package.PortfolioAboutDashboard import show_dashboard
from package.PortfolioRebalancingCore import get_current_price, get_bid_ask_price, BUY_ORDER_DISADVANTAGE_RATE_PCT
import copy
import time


def my_print(to_print: bool, message, end='\n'):
    if to_print:
        print(message, end=end)


def distribute_buyable_cash_core(portfolio_count: int, buyable_cash: float, portfolio_value_list: list, target_ratios: list):
    portfolio_value_total = sum(portfolio_value_list)
    target_ratios_total = sum(target_ratios)

    # 포트폴리오 비율 정규화 (ex. [1, 1, 2] -> [1/4, 1/4, 1/2])
    target_ratios_normalized = [target_ratio / target_ratios_total for target_ratio in target_ratios]

    # 현재평가금액과 목표평가금액 간의 괴리율 계산 (괴리율이 크다 : 목표비율에 크게 미달한다)
    disparate_rate_list = []
    for i in range(portfolio_count):
        expected_portfolio_value = portfolio_value_total * target_ratios_normalized[i]
        disparate_rate_list.append((portfolio_value_list[i] - expected_portfolio_value) / expected_portfolio_value * 100)

    # 괴리율이 제일 큰, 즉 제일 먼저 보충해야 하는 포트폴리오부터 순차적으로 나열
    rank_tuple, _ = zip(*sorted(enumerate(disparate_rate_list), key=lambda x: x[1]))
    rank_list = list(rank_tuple)
    sorted_target_ratios_normalized = [target_ratios_normalized[rank] for rank in rank_list]
    sorted_portfolio_value_list = [portfolio_value_list[rank] for rank in rank_list]

    # ----------------------------------------------------

    # 괴리율이 가장 큰 것부터 그 다음 것의 비율, 그 다음 것의 비율로 맞추는 형태
    sorted_buyable_cash_list = [0] * portfolio_count
    remaining_cash = buyable_cash
    for i in range(portfolio_count):
        if i != portfolio_count - 1:
            # target_ratio가 전부 동일한 가상의 상황을 만들어서 (ex. a:b:c를 a:a:a로 임시변환) 비교하기 쉽게 만듦
            current = sorted_portfolio_value_list[i]
            real_to_virtual_ratio = sorted_target_ratios_normalized[i] / sorted_target_ratios_normalized[i + 1]
            virtual_target = sorted_portfolio_value_list[i + 1] * real_to_virtual_ratio
            full_pieces_of_equalize_amount = 0
            for j in range(i + 1):
                virtual_to_real_ratio = sorted_target_ratios_normalized[j] / sorted_target_ratios_normalized[i]
                a_piece_of_equalize_amount = (virtual_target - current) * virtual_to_real_ratio
                full_pieces_of_equalize_amount += a_piece_of_equalize_amount
            # (리밸런싱을 위해) i + 1번째의 cash를 기준으로 0 ~ i의 비율을 맞추고자 함. 0번째에서 i번째까지 필요한 cash의 양이 모자라는가/충분한가?
            to_equalize_amount = min(remaining_cash, full_pieces_of_equalize_amount)
        else:
            to_equalize_amount = remaining_cash

        # 계산한 결과물을 sorted_portfolio_value_list, sorted_buyable_cash_list, remaining_cash에 반영함
        target_ratios_sum = sum(sorted_target_ratios_normalized[:i+1])
        for j in range(i + 1):
            a_piece_of_to_equalize_amount = to_equalize_amount * sorted_target_ratios_normalized[j] / target_ratios_sum
            sorted_portfolio_value_list[j] += a_piece_of_to_equalize_amount
            sorted_buyable_cash_list[j] += a_piece_of_to_equalize_amount
            remaining_cash -= a_piece_of_to_equalize_amount

    # ----------------------------------------------------

    # 정렬된 리스트를 원래의 순서로 되돌림
    rank_to_index = {rank: index for index, rank in enumerate(rank_list)}
    buyable_cash_list = [sorted_buyable_cash_list[rank_to_index[rank]] for rank in range(len(rank_list))]

    # 반환할 값들의 반올림 처리
    buyable_cash = round(buyable_cash, 4)
    buyable_cash_list = [round(amount, 4) for amount in buyable_cash_list]

    return buyable_cash, buyable_cash_list


def distribute_buyable_cash(buyable_cash: float, portfolio_mkt_qty_dict: dict, target_ratios: list):
    # 구매가능금액을 각각의 포트폴리오 비율에 따라서 배분해주는 함수
    print('Loading...')
    portfolio_count = len(portfolio_mkt_qty_dict)
    portfolio_value_list = [0] * portfolio_count
    for i in range(portfolio_count):
        time.sleep(0.3)  # Running loop below takes about 0.8 second per 20 api calls
        for j, (ticker, mkt_qty_list) in enumerate(portfolio_mkt_qty_dict[f'portfolio_mkt_qty_{i + 1}'].items()):
            if j % 20 == 0 and j // 20 != 0:  # Max 20 requests per second (KIS Developer)
                time.sleep(0.3)
            current_price = get_current_price(ticker, mkt_qty_list[0])
            current_qty = mkt_qty_list[1]
            portfolio_value_list[i] += current_price * current_qty
        portfolio_value_list[i] = round(portfolio_value_list[i], 4)

    buyable_cash, buyable_cash_list = distribute_buyable_cash_core(portfolio_count, buyable_cash, portfolio_value_list, target_ratios)

    print(portfolio_value_list)
    print(buyable_cash_list, '    // ', buyable_cash)
    for i, _ in enumerate(buyable_cash_list):
        print(round(portfolio_value_list[i] + buyable_cash_list[i], 4), end=' ')
    print()
    print('Buyable cash($) of each portfolio has been calculated.\n')

    return buyable_cash, buyable_cash_list


def estimate_original(buyable_cash_dollar: float, **portfolio_dict):
    """목표매매수량을 계산하는 함수. 목표 비율에 맞춘 후 소수점 버림을 하므로, 잔액이 발생 (이는 아래의 adjusted_2 함수에서 해결)"""
    """보유종목 : [자산분류, 시장분류, 단가($), 현재보유량(주), 현재평가금액($), 현재배분율[R](%), (현재배분율[I](%)), 목표보유량(주), 목표평가금액($),
                목표배분율[R](%), (목표배분율[I](%)), 목표매매량(주), 예상매매금액($), 괴리율(%), 매수1호가($), 매도1호가($)]"""
    realtime_total_etfs_dollar = 0.00

    for ticker, lst in portfolio_dict.items():
        market = lst[1]
        current_qty = lst[3]
        current_price = get_current_price(ticker, market)
        bid_price, ask_price = get_bid_ask_price(ticker, market)
        lst[2] = current_price
        lst[4] = current_price * current_qty
        lst[14] = bid_price
        lst[15] = ask_price
        # 실시간으로 업데이트된 현재가를 반영한 현재 보유주식의 총합 (정교한 잔액 파악으로 계산오차를 줄이기 위함)
        realtime_total_etfs_dollar += lst[4]
    """etfs_cash_sum > 0이 아니면, 오류 발생"""
    etfs_cash_sum = realtime_total_etfs_dollar + buyable_cash_dollar

    to_order_etfs_dollar = 0.00
    for ticker, lst in portfolio_dict.items():
        current_price = lst[2]
        current_qty = lst[3]
        target_percentage = lst[10] / 100
        target_qty = int((etfs_cash_sum * target_percentage) // current_price)
        # '괴리율' : 목표배분율(이상값) - 목표배분율(실제값)
        disparate_rate = (current_price * target_qty - etfs_cash_sum * target_percentage) / etfs_cash_sum * 100
        lst[5] = (current_price * current_qty / etfs_cash_sum) * 100
        lst[7] = target_qty
        lst[8] = current_price * target_qty
        lst[9] = current_price * target_qty / etfs_cash_sum * 100
        lst[11] = target_qty - current_qty
        lst[12] = current_price * (target_qty - current_qty)
        lst[13] = round(disparate_rate, 4)
        to_order_etfs_dollar += lst[12]

    return realtime_total_etfs_dollar, to_order_etfs_dollar, portfolio_dict


def assist_adjusted_1(to_show_dashboard: bool, total_etfs_dollar: float, buyable_cash_dollar: float, **portfolio_dict):
    exclusion_etfs_dollar = 0.00  # **현재 열외할 자산금액의 합계 (주문 가능 현금 : buyable_cash_dollar로 배분해야 함)**
    exclusion_current_percentage = 0.00
    exclusion_target_percentage = 0.00
    to_order_etfs_dollar = 0.00  # 앞으로 매수할 자산금액의 합계
    portfolio_dict_adj = {}  # '매수할 종목'만으로 리밸런싱하고자, 목표배분율을 초과하는 자산은 열외

    for ticker, lst in portfolio_dict.items():
        if lst[11] >= 0:
            portfolio_dict_adj[ticker] = copy.deepcopy(portfolio_dict[ticker])  # 깊은복사(테이블 새로만들기)
        else:
            exclusion_etfs_dollar += lst[4]
            exclusion_current_percentage += lst[6]
            exclusion_target_percentage += lst[10]
    total_etfs_dollar_adj = total_etfs_dollar - exclusion_etfs_dollar
    etfs_cash_sum_adj = total_etfs_dollar_adj + buyable_cash_dollar

    for ticker, lst in portfolio_dict_adj.items():
        lst[5] = lst[4] / total_etfs_dollar_adj * 100 if total_etfs_dollar_adj != 0 else 0
        lst[6] = lst[6] / (100 - exclusion_current_percentage) * 100 if 100 - exclusion_current_percentage != 0 else 0
        lst[10] = lst[10] / (100 - exclusion_target_percentage) * 100 if 100 - exclusion_current_percentage != 0 else 0
        lst[7] = int(etfs_cash_sum_adj * (lst[10] / 100) // lst[2])
        lst[8] = lst[2] * lst[7]
        lst[9] = lst[8] / etfs_cash_sum_adj * 100 if etfs_cash_sum_adj != 0 else 0
        lst[11] = lst[7] - lst[3]
        lst[12] = lst[2] * lst[11]
        lst[13] = round((lst[8] - etfs_cash_sum_adj * (lst[10] / 100)) / etfs_cash_sum_adj * 100, 4) if etfs_cash_sum_adj != 0 else 0
        to_order_etfs_dollar += lst[12]

    if to_show_dashboard:
        show_dashboard(total_etfs_dollar_adj, to_order_etfs_dollar, buyable_cash_dollar, **portfolio_dict_adj)

    return total_etfs_dollar_adj, to_order_etfs_dollar, portfolio_dict_adj


def estimate_adjusted_1(to_show_sub_dashboard: bool, total_etfs_dollar: float, buyable_cash_dollar: float, **portfolio_dict):
    """목표매매수량을 'buy-only'로 바꿔주는 함수"""
    total_etfs_dollar_adj = total_etfs_dollar
    portfolio_dict_adj = portfolio_dict

    while True:
        """(매수only 로직을 만들고자) 목표배분율을 초과하는 종목의 목록을 반복문을 돌려서 걸러질 때까지 필터링하고 계산함"""
        until_no_more_etf_to_sell = True
        total_etfs_dollar_adj, to_order_etfs_dollar, portfolio_dict_adj = assist_adjusted_1(to_show_sub_dashboard, total_etfs_dollar_adj,
                                                                                            buyable_cash_dollar, **portfolio_dict_adj)
        for ticker, lst in portfolio_dict_adj.items():
            if lst[11] < 0:
                until_no_more_etf_to_sell = False
                break
            else:
                continue
        if until_no_more_etf_to_sell:
            break

    portfolio_buy_qty_dict = {}
    for ticker in portfolio_dict:
        portfolio_buy_qty_dict[ticker] = 0
    for ticker, lst in portfolio_dict_adj.items():
        if lst[11] > 0:
            portfolio_buy_qty_dict[ticker] = lst[11]

    """etfs_cash_sum > 0이 아니면, 오류 발생"""
    etfs_cash_sum = total_etfs_dollar + buyable_cash_dollar
    to_order_etfs_dollar = 0.00
    for ticker, lst in portfolio_dict.items():
        """위에서 구한 목표매매량은 다시 원래있던 전체 목록에 적용하고 새로운 목표배분율을 구함 """
        current_price = lst[2]
        current_qty = lst[3]
        target_percentage = lst[10] / 100
        target_qty = lst[3] + portfolio_buy_qty_dict[ticker]
        disparate_rate = (current_price * target_qty - etfs_cash_sum * target_percentage) / etfs_cash_sum * 100
        lst[7] = target_qty
        lst[8] = current_price * target_qty
        lst[9] = current_price * target_qty / etfs_cash_sum * 100
        lst[11] = target_qty - current_qty
        lst[12] = current_price * (target_qty - current_qty)
        lst[13] = round(disparate_rate, 4)
        to_order_etfs_dollar += lst[12]

    return total_etfs_dollar, to_order_etfs_dollar, portfolio_dict


def estimate_adjusted_2(to_print_msg: bool, total_etfs_dollar: float, buyable_cash_dollar: float, **portfolio_dict):
    """남은 돈으로 구매 가능한 주식을 마저 사들이는 함수 (아래 계산식은 구매가와 거래수수료를 반영하여 차감)"""
    to_order_etfs_dollar = 0.00
    for ticker, lst in portfolio_dict.items():
        to_order_etfs_dollar += lst[12]
    remaining_cash_dollar = buyable_cash_dollar - to_order_etfs_dollar
    """etfs_cash_sum > 0이 아니면, 오류 발생"""
    etfs_cash_sum = total_etfs_dollar + buyable_cash_dollar

    sell_amount_abs = 0
    for ticker, lst in portfolio_dict.items():
        if lst[12] < 0:
            sell_amount_abs += abs(lst[12])
    my_print(to_print_msg, 'Buy-only는 해당사항 없음, 매도 시 주문가능금액 차감액수 계산(전체 매도금액의 1.068% ~ 1.215% 가량 제외됨)')
    my_print(to_print_msg, '{0:.3f} - {1:.3f}(매도금액의 1.5%) = {2:.3f}'.format(remaining_cash_dollar, sell_amount_abs * 1.5 / 100,
                                                                            remaining_cash_dollar - (sell_amount_abs * 1.5 / 100)))
    remaining_cash_dollar -= sell_amount_abs * 1.5 / 100

    buy_amount_abs = 0
    for ticker, lst in portfolio_dict.items():
        if lst[12] > 0:
            buy_amount_abs += lst[12]
    my_print(to_print_msg, '매수 시 주문가능금액 차감액수 계산(기본 거래수수료인 전체 매수금액의 0.25%로 가정)')
    my_print(to_print_msg, '{0:.3f} - {1:.3f}(매수금액의 0.25%) = {2:.3f}'.format(remaining_cash_dollar, buy_amount_abs * 0.25 / 100,
                                                                             remaining_cash_dollar - (buy_amount_abs * 0.25 / 100)))
    my_print(to_print_msg, '>> 이미 위의 계산표대로 주문하고 난 후, 낱개주문한다고 가정 (즉, 수수료 계산이 보수적임)\n')
    remaining_cash_dollar -= buy_amount_abs * 0.25 / 100

    while True:
        """잔액이 고갈될 때까지 추가주문하는 계산식 (단, '주문금액 = n%상향매수 * 거래수수료 * 현재가' 임을 감안함)"""
        """+1주 했을 경우의 각각의 예상 괴리율(%)을 리스트에 넣고 max sort"""
        """선정된 최우선순위의 주식 +1주"""
        portfolio_disparate_rate_dict: dict[str, float] = {}
        for ticker, lst in portfolio_dict.items():
            portfolio_disparate_rate_dict[ticker] = 100.00

        for ticker, lst in portfolio_dict.items():
            # (1)남아있는 잔액보다 단가가 비싸거나, (2)목표배분율이 0%인 종목은 추가주문대상에서 제외
            if remaining_cash_dollar < lst[2] * (1 + BUY_ORDER_DISADVANTAGE_RATE_PCT / 100) * (1 + 0.25 / 100):
                continue
            elif lst[10] == 0:
                continue
            else:
                evlu_real = lst[2] * (lst[7] + 1)  # 1주를 더 살 경우 해당 종목의 목표평가금액[현실값] (ex. $99.80 * 20주 + $99.80 * 1주)
                evlu_ideal = etfs_cash_sum * (lst[10] / 100)  # 해당 종목의 목표평가금액[이상값] (ex. $10000.00 * 20%)
                evlu_disparate_rate = (evlu_real - evlu_ideal) / etfs_cash_sum * 100  # 해당 주식의 괴리율 계산
                portfolio_disparate_rate_dict[ticker] = evlu_disparate_rate
        # noinspection PyTypeChecker
        portfolio_disparate_rate_dict = dict(sorted(portfolio_disparate_rate_dict.items(), key=lambda x: x[1], reverse=False))
        ticker_to_add = min(portfolio_disparate_rate_dict, key=portfolio_disparate_rate_dict.get)

        for ticker, value in portfolio_disparate_rate_dict.items():
            if value != 100.00:
                my_print(to_print_msg, f"'{ticker}': {value:.4f}", end=' ')

        if portfolio_disparate_rate_dict[ticker_to_add] != 100.00:
            my_print(to_print_msg, f'\n {ticker_to_add:<4} (+1)', end=' ')
        else:
            break

        ticker_to_add_list = portfolio_dict[ticker_to_add]
        ticker_to_add_list[7] = ticker_to_add_list[7] + 1
        ticker_to_add_list[8] = ticker_to_add_list[2] * ticker_to_add_list[7]
        # ticker_to_add_list[9](목표배분율[R])은 cash의 비율을 가져오는 것이므로, 다른 주식의 목표배분율에 영향을 주지 않음
        ticker_to_add_list[9] = ticker_to_add_list[8] / etfs_cash_sum * 100
        ticker_to_add_list[11] = ticker_to_add_list[11] + 1
        ticker_to_add_list[12] = ticker_to_add_list[2] * ticker_to_add_list[11]
        ticker_to_add_list[13] = (ticker_to_add_list[8] - etfs_cash_sum * (ticker_to_add_list[10] / 100)) / etfs_cash_sum * 100
        to_order_etfs_dollar += ticker_to_add_list[2]
        remaining_cash_dollar -= ticker_to_add_list[2] * (1 + BUY_ORDER_DISADVANTAGE_RATE_PCT / 100) * (1 + 0.25 / 100)
        my_print(to_print_msg, '    // ', end='')
        my_print(to_print_msg, f'{1 + BUY_ORDER_DISADVANTAGE_RATE_PCT / 100:.4f} * {1 + 0.25 / 100:.4f} * ${ticker_to_add_list[2]}'
                               f'({BUY_ORDER_DISADVANTAGE_RATE_PCT}%상향매수 * 0.25%거래수수료(가정) * 현재가)로 낱개구매 후 예상잔액 :'
                               f'${remaining_cash_dollar:.2f}\n')

    return total_etfs_dollar, to_order_etfs_dollar, portfolio_dict


def estimate_print_portfolio(buy_only_mode: bool, pf_code: str, buyable_cash_dollar: float, portfolio_dict: dict):
    total_etfs_dollar, to_order_etfs_dollar, _ = estimate_original(buyable_cash_dollar, **portfolio_dict)
    if buy_only_mode:
        total_etfs_dollar, to_order_etfs_dollar, _ = estimate_adjusted_1(False, total_etfs_dollar, buyable_cash_dollar, **portfolio_dict)
    total_etfs_dollar, to_order_etfs_dollar, _ = estimate_adjusted_2(False, total_etfs_dollar, buyable_cash_dollar, **portfolio_dict)
    print(f'portfolio_{pf_code})', end=' ')
    show_dashboard(total_etfs_dollar, to_order_etfs_dollar, buyable_cash_dollar, **portfolio_dict)
    remaining_cash_dollar = buyable_cash_dollar - to_order_etfs_dollar

    return remaining_cash_dollar
