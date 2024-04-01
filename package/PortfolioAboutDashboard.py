from package.PortfolioRebalancingCore import get_portfolio_mkt_qty, get_total_etfs_evlu_dollar, get_asset_info_won, \
    get_buyable_cash_dollar_and_exchange_rate, TRANSACTION_FEE_RATE_PCT


def get_account_info_and_show_briefing():
    portfolio_mkt_qty_dict = get_portfolio_mkt_qty()  # 종목별 시장분류 및 보유수량
    profit_loss_dollar, total_etfs_dollar = get_total_etfs_evlu_dollar()  # etf 평가금액($)
    buyable_cash_dollar, exchange_rate = get_buyable_cash_dollar_and_exchange_rate()  # 주문가능 현금($), 환율(₩/$)
    total_etfs_won, korean_cash_won, us_cash_won, total_assets_won, ustl_buy_amt_etfs_won, ustl_sll_amt_etfs_won = get_asset_info_won()
    expected_final_balance_dollar = (korean_cash_won + us_cash_won + ustl_sll_amt_etfs_won - ustl_buy_amt_etfs_won) / exchange_rate

    # 해외etf평가금액 + 원화예수금 + 해외예수금 - 미결제매수금액 = 총자산
    print(f'[참고용] 해외주식 평가손익($) : ${profit_loss_dollar:>.2f}')
    print(f'-------------------------------------------')
    print(f'해외주식 평가금액($)  : ${total_etfs_dollar:>9.2f}')
    print(f'주문가능 현금($)      : ${buyable_cash_dollar:>9.2f}')
    print(f'결제후 예상 예수금($) : ${expected_final_balance_dollar:>9.2f}')
    print(f'-------------------------------------------')
    print(f'해외주식 평가금액(₩)  : {total_etfs_won:>9}원')
    print(f'원화 예수금(₩)        : {korean_cash_won:>9}원')
    print(f'달러 예수금(₩)        : {us_cash_won:>9}원')
    print(f'미결제 매수금액(₩)    : {-1 * ustl_buy_amt_etfs_won:>9}원')
    print(f'미결제 매도금액(₩)    : {ustl_sll_amt_etfs_won:>9}원')
    print(f'-------------------------------------------')
    print(f'총합계(₩)             : {total_assets_won:>9}원', end=' ')
    print(f'(환율: {exchange_rate})')
    print('\n\n\n')

    return buyable_cash_dollar, portfolio_mkt_qty_dict, expected_final_balance_dollar


def show_dashboard(total_etfs_dollar: float, to_order_etfs_dollar: float, buyable_cash_dollar: float, **portfolio_dict):
    _, korean_cash_won, us_cash_won, _, ustl_buy_amt_etfs_won, ustl_sll_amt_etfs_won = get_asset_info_won()
    _, exchange_rate = get_buyable_cash_dollar_and_exchange_rate()
    balance_dollar = buyable_cash_dollar - to_order_etfs_dollar
    etfs_cash_sum = total_etfs_dollar + buyable_cash_dollar

    transaction_amount_abs = 0
    for ticker, lst in portfolio_dict.items():
        transaction_amount_abs += abs(lst[12])
    print('아래 계산표에 거래수수료(≈${0:.3f})는 포함되지 않음'.format(transaction_amount_abs * TRANSACTION_FEE_RATE_PCT / 100))
    # print('보유종목 : [자산분류, 시장분류, 단가($), 현재보유량(주), 현재평가금액($), 현재배분율[R](%), (현재배분율[I](%)), 목표보유량(주), '
    #       '목표평가금액($), 목표배분율[R](%), (목표배분율[I](%)), 목표매매량(주), 예상매매금액($), 괴리율(%), 매수1호가($), 매도1호가($)]')

    current_rate_sum = buyable_cash_dollar / etfs_cash_sum * 100 if etfs_cash_sum != 0 else 0
    target_rate_sum = (buyable_cash_dollar - to_order_etfs_dollar) / etfs_cash_sum * 100 if etfs_cash_sum != 0 else 0
    buyable_cash_dollar_percentage = buyable_cash_dollar / etfs_cash_sum * 100 if etfs_cash_sum != 0 else 0
    balance_dollar_percentage = balance_dollar / etfs_cash_sum * 100 if etfs_cash_sum != 0 else 0
    for ticker, lst in portfolio_dict.items():
        current_rate_sum += lst[5]
        target_rate_sum += lst[9]
        print(
            '{0:>5} : [{1:>5}| {2:>4}| ${3:>6.2f}| {4:>3}주, ${5:>8.2f},{6:>6.2f}%({7:>5.2f}%)| {8:>3}주, ${9:>8.2f},{10:>6.2f}%'
            '({11:>5.2f}%)|{12:>4}주, ${13:>9.2f},{14:>7.4f}%| ${15:>6.2f}, ${16:>6.2f} ]'.format(
                ticker, lst[0], lst[1], lst[2], lst[3], lst[4], lst[5], lst[6], lst[7], lst[8], lst[9], lst[10], lst[11], lst[12],
                lst[13], lst[14], lst[15]))

    print(' Cash :                      |    ', end='')
    print('(**)${0:>8.2f},{1:>6.2f}%        |        ${2:>8.2f},{3:>6.2f}%        |                           |'.format(
        buyable_cash_dollar, buyable_cash_dollar_percentage, balance_dollar, balance_dollar_percentage))
    print('-----------------------------------------------------------------------------------------------------------------------------')
    print(' $Sum :                      |    ', end='')
    print(' (*)${0:>8.2f},{1:>6.2f}%        |        ${2:>8.2f},{3:>6.2f}%        |        ${4:>8.2f}          |'.format(
        etfs_cash_sum, current_rate_sum, etfs_cash_sum, target_rate_sum, to_order_etfs_dollar))
    print(' ₩Sum :                      |    ', end='')
    print('   {0:>9}원               |       {1:>9}원               |        {2:>8}원         |'.format(
        int(etfs_cash_sum * exchange_rate), int(etfs_cash_sum * exchange_rate), int(to_order_etfs_dollar * exchange_rate)))
    print('(*    : 해외주식평가금[실시간](${0:>.2f})에 주문가능현금(${1:>.2f})을 더한 값)'.format(total_etfs_dollar, buyable_cash_dollar))
    print()

    return portfolio_dict
