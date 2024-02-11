from package.PortfolioAboutDashboard import get_account_info_and_show_briefing
from package.PortfolioRebalancingCore import check_token_expired, send_message
from package.PortfolioCalculatorCore import distribute_buyable_cash, estimate_print_portfolio
from package.PortfolioCalculatorAuth import path_google_sheet, auth_google_sheet, auth_google_file, open_json_file
from package.PortfolioCalculatorDuplicate import find_existing_sheet_and_duplicate
from package.PortfolioCalculatorFillPurple import get_exchange_rate_from_google_sheet, get_pointer_ticker_plate_from_google_sheet, \
    do_ticker_duplicate_check, send_material_to_plate_and_do_ticker_missing_check, get_mkt_info_from_ticker_book, \
    print_portfolio_mkt_qty_from_google_sheet, backup_portfolio_mkt_qty_info_to_json_file, put_mkt_and_qty_to_google_sheet, \
    put_cash_to_google_sheet
from package.PortfolioCalculatorFillRed import unpack_portfolio_data, get_infos_from_google_sheet_and_json, put_portfolio_to_json_file, \
    put_target_qty_to_google_sheet, put_remaining_cash_and_update_date_to_google_sheet, check_backup_file_created_within_five_minutes
import datetime
import time


# default : '*dashboard', [1, 2], [3], [1, 1, 1]
SHEET_NAME = '*dashboard'  # google-sheet.json
PF_BUY_ONLY_LIST = [1, 2]
PF_TO_IMPORT_MKT_LIST = [3]
FUND_RATIO = [1, 1, 1]


def three_new_lines():
    print('\n\n\n')


def main():
    check_token_expired()
    buyable_cash_dollar_sum, material_mkt_qty_dict, expected_final_balance_dollar = get_account_info_and_show_briefing()

    """-------------------------------------------------------------------------------------------"""

    print('PortfolioCalculatorFillPurple.py---------------------------------------------------------')

    g_start_time = time.time()
    spreadsheet_url = path_google_sheet()
    worksheet1 = auth_google_sheet('excel-editor-1.json', spreadsheet_url, SHEET_NAME)
    print()

    # Input, Process(from Google Sheet and ticker book : including missing/duplicate check)
    exchange_rate = get_exchange_rate_from_google_sheet(worksheet1)
    row_pointer_dict, portfolio_ticker_list, plate_portfolio_mkt_qty_dict = get_pointer_ticker_plate_from_google_sheet(worksheet1)
    plate_portfolio_mkt_qty_dict['portfolio_mkt_qty_1'] = {'BRK/B' if ticker == 'BRK.B' else ticker: lst for ticker, lst in
                                                           plate_portfolio_mkt_qty_dict['portfolio_mkt_qty_1'].items()}
    portfolio_mkt_qty_dict = send_material_to_plate_and_do_ticker_missing_check(material_mkt_qty_dict, plate_portfolio_mkt_qty_dict)
    do_ticker_duplicate_check(portfolio_ticker_list)
    for mkt_val in PF_TO_IMPORT_MKT_LIST:
        get_mkt_info_from_ticker_book(portfolio_mkt_qty_dict, mkt_val)  # 신규 편입된 종목을 이 함수에서 세탁(?)하지 않으면 ''로 ValueError 발생
    buyable_cash_dollar_sum, buyable_cash_dollar_list = distribute_buyable_cash(buyable_cash_dollar_sum, portfolio_mkt_qty_dict,
                                                                                FUND_RATIO)
    print_portfolio_mkt_qty_from_google_sheet(worksheet1, row_pointer_dict, portfolio_mkt_qty_dict)

    # Backup(to .json)
    backup_portfolio_mkt_qty_info_to_json_file(row_pointer_dict, exchange_rate, buyable_cash_dollar_sum, buyable_cash_dollar_list,
                                               portfolio_mkt_qty_dict)

    # Output(to Google Sheet)
    put_mkt_and_qty_to_google_sheet(worksheet1, row_pointer_dict, portfolio_mkt_qty_dict, PF_TO_IMPORT_MKT_LIST)
    put_cash_to_google_sheet(worksheet1, row_pointer_dict, exchange_rate, expected_final_balance_dollar, buyable_cash_dollar_list)

    g_end_time = time.time()
    print(f'실행 시간: {g_end_time - g_start_time:.5f} 초\n')
    three_new_lines()

    """-------------------------------------------------------------------------------------------"""

    print('PortfolioCalculatorDuplicate.py----------------------------------------------------------')
    """Duplicate Google Worksheet: *dashboard -> 20240101"""

    g_start_time = time.time()
    spreadsheet_url = path_google_sheet()
    book = auth_google_file('excel-editor-1.json', spreadsheet_url)
    print()

    # Input, Process(from Google Sheet)
    existing_sheet_name = SHEET_NAME
    to_copy_sheet_name = datetime.datetime.now().strftime('%Y%m%d')  # ex. 20240101
    to_copy_sheet_name = find_existing_sheet_and_duplicate(existing_sheet_name, to_copy_sheet_name, book)

    g_end_time = time.time()
    print(f'실행 시간: {g_end_time - g_start_time:.5f} 초\n')
    three_new_lines()

    """-------------------------------------------------------------------------------------------"""

    print('PortfolioCalculatorFillRed.py------------------------------------------------------------')

    g_start_time = time.time()
    spreadsheet_url = path_google_sheet()
    worksheet2 = auth_google_sheet('excel-editor-2.json', spreadsheet_url, to_copy_sheet_name)
    print()

    # Input(from Google Sheet and backup file)
    portfolio_mkt_qty_info = open_json_file('./config/backup-portfolio-mkt-qty-info.json')
    check_backup_file_created_within_five_minutes(portfolio_mkt_qty_info)
    row_pointer_dict, exchange_rate, buyable_cash_dollar_list, portfolio_mkt_qty_dict = unpack_portfolio_data(portfolio_mkt_qty_info)
    portfolio_dicts = get_infos_from_google_sheet_and_json(worksheet2, row_pointer_dict, portfolio_mkt_qty_dict)

    # Process
    remaining_cash_dollar_list = []
    for i, _ in enumerate(portfolio_dicts):
        buy_only_mode = True if i + 1 in PF_BUY_ONLY_LIST else False
        remaining_cash_dollar = estimate_print_portfolio(buy_only_mode, str(i + 1), buyable_cash_dollar_list[i], portfolio_dicts[i])
        remaining_cash_dollar_list.append(round(remaining_cash_dollar, 4))

    # Save(to .json)
    put_portfolio_to_json_file(buyable_cash_dollar_list, remaining_cash_dollar_list, portfolio_dicts)

    # Output(to Google Sheet)
    portfolio_dicts[0] = {'BRK.B' if ticker == 'BRK/B' else ticker: lst for ticker, lst in portfolio_dicts[0].items()}
    put_target_qty_to_google_sheet(worksheet2, row_pointer_dict, portfolio_dicts)
    put_remaining_cash_and_update_date_to_google_sheet(worksheet2, row_pointer_dict, exchange_rate, remaining_cash_dollar_list)
    send_message('포트폴리오를 스프레드시트에서 불러왔습니다. 리밸런싱을 위한 계산을 마쳐서, 결과지를 저장합니다.')
    print()

    g_end_time = time.time()
    print(f'실행 시간: {g_end_time - g_start_time:.5f} 초\n')


main()
