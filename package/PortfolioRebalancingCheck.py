from package.PortfolioRebalancingCore import send_message, get_portfolio_mkt_qty
import datetime


def send_message_with_disqualification(msg):
    is_disqualified = True
    send_message(msg)

    return is_disqualified


def check_backup_file_created_within_twenty_for_hours(portfolio_outputs: list):
    is_disqualified = False

    for i, portfolio_output in enumerate(portfolio_outputs):
        update_date_str = portfolio_output['update_date']
        update_date = datetime.datetime.strptime(update_date_str, '%Y-%m-%d %H:%M:%S')
        current_date = datetime.datetime.now()
        twenty_four_hours_ago = current_date - datetime.timedelta(hours=24)
        is_within_twenty_four_hours = update_date >= twenty_four_hours_ago
        if not is_within_twenty_four_hours:
            is_disqualified = send_message_with_disqualification(f'./output/portfolio_output_{i + 1}.json이 만들어진지 24시간 이상이 경과함')

    if is_disqualified:
        raise Exception(f'경고! 오래된 자료로 잘못된 거래를 할 위험이 있어 종료합니다. 자료를 업데이트하고 다시 시도하세요.')


def check_portfolio_mkt_qty(portfolio_dicts: list):
    is_disqualified = False

    from_api_mkt_qty_dict_unsorted = get_portfolio_mkt_qty()
    from_api_mkt_qty_dict = {}
    for portfolio_dict in portfolio_dicts:
        for ticker in portfolio_dict.keys():
            from_api_mkt_qty_dict[ticker] = []  # api에서 가져온 정보를 Google Sheet 순서로 정렬시키는 작업
    for ticker in from_api_mkt_qty_dict_unsorted.keys():
        from_api_mkt_qty_dict[ticker] = from_api_mkt_qty_dict_unsorted[ticker]

    from_gsheet_mkt_qty_dict = {}
    for portfolio_dict in portfolio_dicts:
        for ticker, lst in portfolio_dict.items():
            from_gsheet_mkt_qty_dict[ticker] = [lst[1], lst[3]]  # 내용물 변경 없다면, deepcopy 안해도 됨

    for ticker, from_api_mkt_qty_list in from_api_mkt_qty_dict.items():
        if ticker not in from_gsheet_mkt_qty_dict:
            is_disqualified = send_message_with_disqualification(f'{ticker} : 기록(.json)에서 누락됨')  # 한투현황 ⊂ 기획서 (e.g.신규추가)
        else:
            if not from_api_mkt_qty_list:
                if from_gsheet_mkt_qty_dict[ticker][1] != 0:
                    is_disqualified = send_message_with_disqualification(f'{ticker} : 현재보유수량 불일치')
            elif from_api_mkt_qty_list[1] != from_gsheet_mkt_qty_dict[ticker][1]:
                is_disqualified = send_message_with_disqualification(f'{ticker} : 현재보유수량 불일치')
            elif from_api_mkt_qty_list[0] != from_gsheet_mkt_qty_dict[ticker][0]:
                is_disqualified = send_message_with_disqualification(f'{ticker} : 시장분류 불일치')

    if is_disqualified:
        raise Exception('경고! 착오로 잘못된 거래를 할 위험이 있어 종료합니다. 자료를 업데이트하고 다시 시도하세요.')


def convert_to_portfolio_mkt_qty_dict(portfolio_dicts: list):
    portfolio_mkt_qty_dict = {}
    for i, portfolio_dict in enumerate(portfolio_dicts):
        portfolio_mkt_qty_dict.update(
            {f'portfolio_mkt_qty_{i + 1}': {ticker: [lst[1], lst[3]] for ticker, lst in portfolio_dict.items()}})

    return portfolio_mkt_qty_dict


def show_ccnl_nccs_concisely(today_order_dict_full_version: dict, portfolio_dicts: list):
    # 당일의 체결내역, 미체결내역을 보여줌
    if today_order_dict_full_version:
        today_concluded_order_dict = {}
        for ticker, sb_lst in today_order_dict_full_version.items():
            if (sb_lst[0] and sb_lst[0][1] != 0) or (sb_lst[1] and sb_lst[1][1] != 0):
                today_concluded_order_dict[ticker] = 0
                today_concluded_order_dict[ticker] -= sb_lst[0][1] if sb_lst[0] and sb_lst[0][1] != 0 else 0
                today_concluded_order_dict[ticker] += sb_lst[1][1] if sb_lst[1] and sb_lst[1][1] != 0 else 0
        """before) {'A': ['', [10, 0, 0, 'buy']], 'B': [[12, 12, 0, 'sell'], [6, 3, 0, 'buy']], 'C': ['', [9, 9, 0, 'buy']]}"""
        """after)  {'A': 10, 'B': -9, 'C': 9}"""

        today_non_ccld_order_dict = {}
        for ticker, sb_lst in today_order_dict_full_version.items():
            if (sb_lst[0] and sb_lst[0][0] - sb_lst[0][1] != 0) or (sb_lst[1] and sb_lst[1][0] - sb_lst[1][1] != 0):
                today_non_ccld_order_dict[ticker] = 0
                today_non_ccld_order_dict[ticker] -= sb_lst[0][0] - sb_lst[0][1] if sb_lst[0] and sb_lst[0][0] - sb_lst[0][1] != 0 else 0
                today_non_ccld_order_dict[ticker] += sb_lst[1][0] - sb_lst[1][1] if sb_lst[1] and sb_lst[1][0] - sb_lst[1][1] != 0 else 0
        """before) {'B': [6, 3, 0, 'buy']}"""
        """after)  {'B': 3}"""

        today_concluded_order_dicts = []
        today_non_ccld_order_dicts = []
        for portfolio_dict in portfolio_dicts:
            sorted_today_concluded_order_dict = {}
            sorted_today_not_ccld_order_dict = {}
            for ticker in portfolio_dict.keys():  # 위에서 보았듯이, Google Sheet의 포트폴리오 순서로 정렬시키는 작업
                if ticker in today_concluded_order_dict:
                    sorted_today_concluded_order_dict[ticker] = today_concluded_order_dict[ticker]
                if ticker in today_non_ccld_order_dict:
                    sorted_today_not_ccld_order_dict[ticker] = today_non_ccld_order_dict[ticker]
            today_concluded_order_dicts.append(sorted_today_concluded_order_dict)
            today_non_ccld_order_dicts.append(sorted_today_not_ccld_order_dict)
        print('체결내역  :', today_concluded_order_dicts)
        print('미체결내역:', today_non_ccld_order_dicts)
        """체결내역  : [{}, {'A': 10, 'B': -9, 'C': 9}, {'D': -5, 'E': -5, 'F': 17, 'G': 29, 'H': -18, 'I': 20}]"""
        """미체결내역: [{}, {'B': 3}, {}]"""
