from gspread import Worksheet
from package.PortfolioRebalancingCore import get_portfolio_mkt_qty
from package.PortfolioRebalancingCore import get_buyable_cash_dollar_and_exchange_rate


def get_info_ki_from_google_sheet(worksheet: Worksheet, row_base_pointer: int):
    row_stack_pointer = 0
    row_pointer = row_base_pointer
    portfolio_input = {}
    print('Loading...')
    print('(import)')

    while True:
        ticker = worksheet.cell(row_pointer, 1).value
        if ticker == '(buyable_cash)':
            row_stack_pointer = row_pointer
            print(f'g_row_stack_pointer_ki : {row_stack_pointer}\n')
            break
        portfolio_input[ticker] = ['', '', 0]
        row_pointer += 1
        print(ticker)

    buyable_cash_won = int(worksheet.cell(row_stack_pointer, 8).value.lstrip('₩').replace(',', ''))
    print(f'{row_stack_pointer} - {row_base_pointer} = {row_stack_pointer - row_base_pointer}', end=' ')
    print(f'(총 {row_stack_pointer - row_base_pointer} 종목 : 기존종목, 신규종목, 이탈종목 포함)')
    print("Received 'portfolio_input_ki' from Google Sheet.\n")

    return row_stack_pointer, buyable_cash_won, portfolio_input


def get_qty_from_kis_developers(**portfolio_input):
    portfolio_mkt_qty_dict = get_portfolio_mkt_qty()
    print('Loading...')

    for ticker, check_list in portfolio_mkt_qty_dict.items():
        if ticker in portfolio_input:
            # if portfolio_dict[ticker][1] != check_list[0]:
            #     raise Exception(f'{ticker} : 해당종목의 시장분류 불일치')  # 'overseas_stock_code.xlsx'가 정확하다면 여기 걸릴 일은 없을듯 함
            portfolio_input[ticker][2] = check_list[1]
        else:
            raise Exception(f'{ticker} : (구글시트에서) 해당종목의 보유기록 누락')
    print("Checked market data, received current qty from KIS Developers to 'portfolio_input_ki'.\n")

    return portfolio_input


def get_buyable_cash_from_kis_developers():
    buyable_cash_dollar, exchange_rate = get_buyable_cash_dollar_and_exchange_rate()
    buyable_cash_won = buyable_cash_dollar * exchange_rate

    return buyable_cash_won


def put_mkt_qty_cash_to_google_sheet(worksheet: Worksheet, row_base_pointer: int, row_stack_pointer: int, buyable_cash_won: int, **portfolio_input):
    row_pointer = row_base_pointer
    print('Loading...')
    print('(export)')

    all_zero_or_invalid = True
    for index, (ticker, list) in enumerate(portfolio_input.items()):
        if list[2]:
            all_zero_or_invalid = False

    for index, (ticker, list) in enumerate(portfolio_input.items()):
        """list = ['', market, current_qty]"""
        worksheet.update_cell(row_pointer, 4, list[1])
        if not all_zero_or_invalid:
            worksheet.update_cell(row_pointer, 7, list[2])
        row_pointer += 1
        print(ticker)
    worksheet.update_cell(row_stack_pointer, 8, buyable_cash_won)
    print("Updated market data, current qty of 'portfolio_input_ki' to Google Sheet.\n")
