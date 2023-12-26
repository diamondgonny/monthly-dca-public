from gspread import Worksheet
from package.PortfolioCalculatorCore import estimate_original
from package.PortfolioCalculatorCore import estimate_adjusted_2
from package.PortfolioRebalancingPrint import show_dashboard
import datetime
import json


def get_portfolio_from_google_sheet_ki_1(worksheet: Worksheet, row_base_pointer: int, row_stack_pointer: int):
    """구글시트 API가 감당 가능한 종목 수는, (60 - 3) / 3 = 최대 19개 정도 까지로 확인됨 (API 호출 시마다 약간의 오차 존재)"""
    row_pointer = row_base_pointer
    portfolio_input = {}
    print('Loading...')
    print('(import)')

    try:
        exchange_rate = float(worksheet.cell(2, 20).value.lstrip('₩').replace(',', ''))
    except Exception as e:
        with open('./config/backup-exchange-rate.json', 'r', encoding='UTF-8') as f:
            exchange_rate_output = json.load(f)
        update_date_str = exchange_rate_output['update_date']
        update_date = datetime.datetime.strptime(update_date_str, "%Y-%m-%d %H:%M:%S")
        current_date = datetime.datetime.now()
        exchange_rate = exchange_rate_output['exchange_rate']
        is_today = update_date.date() == current_date.date()
        if is_today:
            print(f'{e}: ./config/backup-exchange-rate.json 에 있는 환율데이터로 대체합니다.')
            print(f'{update_date} 기준 환율 : {exchange_rate}\n')
        else:
            raise Exception('오래된 환율데이터 입니다(오늘X). 환율데이터를 업데이트 하세요.')

    existing_balance_won = int(worksheet.cell(row_stack_pointer, 8).value.lstrip('₩').replace(',', ''))
    new_balance_won = int(worksheet.cell(row_stack_pointer, 16).value.lstrip('₩').replace(',', ''))
    buyable_cash_dollar = (existing_balance_won + new_balance_won) / exchange_rate

    while True:
        ticker = worksheet.cell(row_pointer, 1).value
        asset_class = worksheet.cell(row_pointer, 3).value
        # market = worksheet_g.cell(row_pointer, 4).value  # 'overseas_stock_code.xlsx'에서 추출 가능함
        current_qty = int(worksheet.cell(row_pointer, 7).value)
        input_list = ['', '', 0, 0, 0]
        input_list[0] = asset_class if asset_class is not None else ''
        input_list[1] = '(market)'
        input_list[2] = current_qty if current_qty is not None else 0
        portfolio_input[ticker] = input_list
        row_pointer += 1
        print(ticker)
        if row_pointer == row_stack_pointer:
            break
    print(f'{row_stack_pointer} - {row_base_pointer} = {row_stack_pointer - row_base_pointer}', end=' ')
    print(f'(총 {row_stack_pointer - row_base_pointer} 종목 : 기존종목, 신규종목, 이탈종목 포함)')
    print("Received 'portfolio_input_ki' from Google Sheet : (1/2)\n")

    return buyable_cash_dollar, portfolio_input


def get_portfolio_from_google_sheet_ki_2(worksheet: Worksheet, row_base_pointer: int, row_stack_pointer: int, **portfolio_input):
    row_pointer = row_base_pointer
    print('Loading...')
    print('(import)')

    """ current_qty, current_pct, target_pct를 처음부터 int로 바꿔라!"""
    for index, (ticker, input_list) in enumerate(portfolio_input.items()):
        current_pct = int(worksheet.cell(row_pointer, 10).value.rstrip('%'))
        target_pct = int(worksheet.cell(row_pointer, 14).value.rstrip('%'))
        input_list[3] = current_pct if current_pct is not None else 0
        input_list[4] = target_pct if target_pct is not None else 0
        row_pointer += 1
        print(ticker)
    print(f'{row_stack_pointer} - {row_base_pointer} = {row_stack_pointer - row_base_pointer}', end=' ')
    print(f'(총 {row_stack_pointer - row_base_pointer} 종목 : 기존종목, 신규종목, 이탈종목 포함)')
    print("Received 'portfolio_input_ki' from Google Sheet : (2/2)\n")

    return portfolio_input


def estimate_portfolio_and_show_progress_ki(buyable_cash_dollar: float, **portfolio_dict):
    total_etfs_dollar, to_order_etfs_dollar, portfolio_dict = estimate_original(buyable_cash_dollar, **portfolio_dict)
    print('estimate_original)', end=' ')
    show_dashboard(total_etfs_dollar, buyable_cash_dollar, to_order_etfs_dollar, False, **portfolio_dict)
    total_etfs_dollar, to_order_etfs_dollar, portfolio_dict = estimate_adjusted_2(total_etfs_dollar, buyable_cash_dollar, **portfolio_dict)
    print('estimate_adjusted)', end=' ')
    show_dashboard(total_etfs_dollar, buyable_cash_dollar, to_order_etfs_dollar, False, **portfolio_dict)

    return buyable_cash_dollar, portfolio_dict
