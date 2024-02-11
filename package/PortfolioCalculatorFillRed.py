from gspread import Worksheet
from package.PortfolioRebalancingCore import get_current_price
import datetime
import json
import time


def check_backup_file_created_within_five_minutes(portfolio_mkt_qty_info: dict):
    update_date_str = portfolio_mkt_qty_info['update_date']
    update_date = datetime.datetime.strptime(update_date_str, '%Y-%m-%d %H:%M:%S')
    current_date = datetime.datetime.now()
    five_minutes_ago = current_date - datetime.timedelta(minutes=5)
    is_within_five_minutes = update_date >= five_minutes_ago
    if not is_within_five_minutes:
        raise Exception('자료가 만들어진지 5분이 지났습니다. 자료를 업데이트하고 다시 시도하세요.')


def unpack_portfolio_data(portfolio_mkt_qty_info: dict):
    row_pointer_dict = portfolio_mkt_qty_info['row_pointer_dict']
    exchange_rate = portfolio_mkt_qty_info['exchange_rate']
    buyable_cash_dollar_list = portfolio_mkt_qty_info['buyable_cash_dollar_list']
    portfolio_mkt_qty_dict = portfolio_mkt_qty_info['portfolio_mkt_qty_dict']
    print('Loading...')

    return row_pointer_dict, exchange_rate, buyable_cash_dollar_list, portfolio_mkt_qty_dict


def get_infos_from_google_sheet_and_json(worksheet: Worksheet, row_pointer_dict: dict, portfolio_mkt_qty_dict: dict):
    portfolio_dicts = []
    portfolio_count = len(portfolio_mkt_qty_dict)
    for i in range(portfolio_count):
        ranges = []
        for c in ['C', 'J', 'N']:
            ranges.append(f"{c}{row_pointer_dict[f'row_base_pointer_{i + 1}']}:{c}{row_pointer_dict[f'row_stack_pointer_{i + 1}'] - 1}")
            """['C10:C15', 'J10:J15', 'N10:N15']"""
        nested_str_downloaded_data = worksheet.batch_get(ranges)  # 가져올 값 : 자산분류, 현재배분율, 목표배분율
        """[[['BOND'], ['STOCK'], ['STOCK'], ...], [['40%'], ['20%'], ['10%'], ...], [['40%'], ['20%'], ['10%'], ...]]"""
        str_downloaded_data = [[element[0] for element in sublist] for sublist in nested_str_downloaded_data]
        """[['BOND', 'STOCK', 'STOCK', 'STOCK', ...], ['40%', '20%', '10%', '10%', ...], ['40%', '20%', '10%', '10%', ...]]"""
        asset_class_list = str_downloaded_data[0]
        current_pct_list = [int(element.rstrip('%')) for element in str_downloaded_data[1]]
        target_pct_list = [int(element.rstrip('%')) for element in str_downloaded_data[2]]

        portfolio_dict = {}
        if i == portfolio_count - 1:  # Running loop below takes about 0.9 second per 20 api calls
            time.sleep(0.2)
        for j, (ticker, mkt_qty_list) in enumerate(portfolio_mkt_qty_dict[f'portfolio_mkt_qty_{i + 1}'].items()):
            if j % 20 == 0 and j // 20 != 0:  # Max 20 requests per second (KIS Developer)
                time.sleep(0.2)
            asset_class = asset_class_list[j]
            market = mkt_qty_list[0]
            current_price = get_current_price(ticker, market)
            current_qty = mkt_qty_list[1]
            current_pct = current_pct_list[j]
            target_pct = target_pct_list[j]
            lst = [asset_class, market, current_price, current_qty, 0, 0, current_pct, 0, 0, 0, target_pct, 0, 0, 0, 0, 0]
            #  보유종목 : [자산분류, 시장분류, 단가($), 현재보유량(주), 현재평가금액($), 현재배분율[R](%), (현재배분율[I](%)), 목표보유량(주), 목표평가금액($),
            #           목표배분율[R](%), (목표배분율[I](%)), 예상매매수량(주), 예상매매금액($), 괴리율(%), 매수1호가($), 매도1호가($)]
            portfolio_dict[ticker] = lst
        portfolio_dicts.append(portfolio_dict)
    time.sleep(0.2)
    print(f"Received 'portfolio_dict' from Google Sheet(asset_class, crnt_qty, tgt_qty), backup-portfolio-mkt-qty-info.json.\n")
    print('Loading...')

    return portfolio_dicts


def put_portfolio_to_json_file(buyable_cash_dollar_list: list, expected_remaining_cash_dollar_list: list, portfolio_dicts: list):
    for i, _ in enumerate(portfolio_dicts):
        update_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        portfolio_output = {
            f'update_date': update_date,
            f'buyable_cash_dollar_{i + 1}': buyable_cash_dollar_list[i],
            f'expected_remaining_cash_dollar_{i + 1}': expected_remaining_cash_dollar_list[i],
            f'portfolio_dict_{i + 1}': portfolio_dicts[i]
        }
        with open(f'./output/portfolio_output_{i + 1}.json', 'w', encoding='UTF-8') as f:
            json.dump(portfolio_output, f, indent=2, sort_keys=False)
            print(f'Saved the portfolio calculation output in ./output/portfolio_output_{i + 1}.json.')
    print()


def put_target_qty_to_google_sheet(worksheet: Worksheet, row_pointer_dict: dict, portfolio_dicts: list):
    ranges = []
    values = []
    for i, _ in enumerate(portfolio_dicts):
        ranges.append(f"K{row_pointer_dict[f'row_base_pointer_{i + 1}']}:K{row_pointer_dict[f'row_stack_pointer_{i + 1}'] - 1}")
        values.append([[lst[7]] for ticker, lst in portfolio_dicts[i].items()])

    update_requests = [{'range': r, 'values': v} for r, v in zip(ranges, values)]
    worksheet.batch_update(update_requests)
    print(f"Updated target qty of portfolios to Google Sheet.")


def put_remaining_cash_and_update_date_to_google_sheet(worksheet: Worksheet, row_pointer_dict: dict, exchange_rate: float,
                                                       remaining_cash_dollar_list: list):
    portfolio_count = len(remaining_cash_dollar_list)
    for i in range(portfolio_count):
        worksheet.update_cell(row_pointer_dict[f'row_stack_pointer_{i + 1}'], 17, remaining_cash_dollar_list[i] * exchange_rate)
    update_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    worksheet.update_cell(2, 19, update_date)
    print(f"Updated datetime, remaining cash of portfolios to Google Sheet.\n")
