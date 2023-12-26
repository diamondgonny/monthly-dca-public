from package.PortfolioRebalancingCore import *


def check_ordered_qty(**portfolio_dict):
    portfolio_ordered_qty_dict_prototype = get_inquire_ccnl()
    portfolio_ordered_qty_dict = {}

    try:
        if portfolio_ordered_qty_dict_prototype:
            for ticker in portfolio_dict.keys():  # 기록상의 지표와 전산상의 지표간의 순서정렬 일치작업
                portfolio_ordered_qty_dict[ticker] = 0  # {(ticker): (ordered_qty), ...}
            for ticker, sell_buy_list in portfolio_ordered_qty_dict_prototype.items():  # api에서 가져온 주문종목들
                if ticker not in portfolio_ordered_qty_dict:
                    raise Exception(f'{ticker} : 보유기록 누락(.json 기록지 업데이트 요망)')
                if sell_buy_list[0]:
                    sell_ordered_qty = sell_buy_list[0][0]
                    portfolio_ordered_qty_dict[ticker] -= sell_ordered_qty
                if sell_buy_list[1]:
                    buy_ordered_qty = sell_buy_list[1][0]
                    portfolio_ordered_qty_dict[ticker] += buy_ordered_qty

            # Check(print) : portfolio_dict[ticker][11] = (기록상의 목표주문수량), portfolio_ordered_qty_dict[ticker] = (전산상의 현재주문수량)
            for ticker, list in portfolio_dict.items():
                print(f"'{ticker}': {list[11]}", end=' ')
            print('-> .json 기록상의 목표주문량')
            print(f'{portfolio_ordered_qty_dict} -> 한투api 전산상의 매매주문량 총합(뉴욕거래소 기준 당일)')
            for ticker, value in portfolio_ordered_qty_dict.items():
                if ticker in portfolio_dict:
                    if value != portfolio_dict[ticker][11]:  # ordered_qty
                        raise Exception(f'{ticker} : 주문수량 불일치(.json 기록지 업데이트 요망)')
            print('***** 일치 *****')
    except Exception as err:
        send_message(f'[오류 발생]{err}')
    return portfolio_ordered_qty_dict_prototype


def check_portfolio_mkt_qty(**portfolio_dict):
    portfolio_mkt_qty_dict_prototype = get_portfolio_mkt_qty()
    portfolio_mkt_qty_dict = {}
    portfolio_market_is_verified: bool = True
    portfolio_current_qty_is_verified: bool = True
    portfolio_ticker_is_not_found: bool = False

    try:
        for ticker in portfolio_dict.keys():  # 기록상의 지표와 전산상의 지표간의 순서정렬 일치작업
            portfolio_mkt_qty_dict[ticker] = []  # {(ticker): [(market), (current_qty)], ...}
        for ticker in portfolio_mkt_qty_dict_prototype.keys():
            portfolio_mkt_qty_dict[ticker] = portfolio_mkt_qty_dict_prototype[ticker]

        # Check(print) : portfolio_dict[ticker][n] = (기록상의 지표), check_list[n] = (전산상의 지표)
        for ticker, list in portfolio_dict.items():
            print(f"'{ticker}': ['{list[1]}', {list[3]}]", end=' ')
        print('-> .json 기록상의 시장분류, 현재보유량')
        print(f'{portfolio_mkt_qty_dict} -> 한투api 전산상의 시장분류, 현재보유량')
        for ticker, check_list in portfolio_mkt_qty_dict.items():
            if ticker in portfolio_dict:
                if not check_list:                                # current_qty(0)
                    if portfolio_dict[ticker][3] != 0:
                        portfolio_current_qty_is_verified = False
                        raise Exception(f'{ticker} : 보유수량 불일치')
                elif check_list[0] != portfolio_dict[ticker][1]:  # market
                    portfolio_market_is_verified = False
                    raise Exception(f'{ticker} : 시장분류 불일치')
                elif check_list[1] != portfolio_dict[ticker][3]:  # current_qty
                    portfolio_current_qty_is_verified = False
                    raise Exception(f'{ticker} : 보유수량 불일치')
            else:
                portfolio_ticker_is_not_found = True
                raise Exception(f'{ticker} : 보유기록 누락')
    except Exception as err:
        send_message(f'[오류 발생]{err}')
    return portfolio_market_is_verified, portfolio_current_qty_is_verified, portfolio_ticker_is_not_found
