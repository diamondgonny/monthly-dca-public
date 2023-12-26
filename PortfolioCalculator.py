from package.PortfolioRebalancingCore import check_token_expired
from package.PortfolioCalculatorCommon import path_google_sheet, auth_google_sheet, get_market_from_ticker_book, auth_google_file
from package.PortfolioCalculatorCommon import convert_portfolio_to_estimate, put_portfolio_to_json_file
from package.PortfolioCalculatorFillPurple import get_info_ki_from_google_sheet, get_qty_from_kis_developers
from package.PortfolioCalculatorFillPurple import get_buyable_cash_from_kis_developers, put_mkt_qty_cash_to_google_sheet
from package.PortfolioCalculatorDuplicate import find_existing_sheet, backup_exchange_rate, put_excel_url_sheet_name_to_json_file
from package.PortfolioCalculatorKI import get_portfolio_from_google_sheet_ki_1, get_portfolio_from_google_sheet_ki_2
from package.PortfolioCalculatorKI import estimate_portfolio_and_show_progress_ki
from package.PortfolioCalculatorNH import get_portfolio_from_google_sheet_nh, estimate_portfolio_and_show_progress_nh
from package.PortfolioCalculatorFillRed import open_json_file, check_portfolio_month, unpack_portfolio_data, print_portfolio
from package.PortfolioCalculatorFillRed import put_target_qty_to_google_sheet
import datetime
import time


g_start_time = time.time()
ROW_BASE_POINTER_NH1 = 2
ROW_STACK_POINTER_NH1 = 8
ROW_BASE_POINTER_NH2 = 12
ROW_STACK_POINTER_NH2 = 21
ROW_BASE_POINTER_KI = 26
g_row_stack_pointer_ki = 0


def five_new_lines():
    print('\n\n\n\n\n')


def main():
    global g_start_time
    global g_row_stack_pointer_ki

    """-------------------------------------------------------------------------------------------"""

    print('PortfolioCalculatorFillPurple.py---------------------------------------------------------')
    g_start_time = time.time()
    check_token_expired()
    spreadsheet_url, _ = path_google_sheet()

    # Input
    worksheet = auth_google_sheet('excel-editor-1.json', spreadsheet_url, '*dashboard')
    g_row_stack_pointer_ki, buyable_cash_won_ki, portfolio_input_ki = get_info_ki_from_google_sheet(worksheet, ROW_BASE_POINTER_KI)

    # Process
    portfolio_input_ki = get_market_from_ticker_book('ki', **portfolio_input_ki)
    # portfolio_input_ki = get_qty_from_kis_developers(**portfolio_input_ki)
    # buyable_cash_won_ki = get_buyable_cash_from_kis_developers()

    # Output(Google Sheet)
    put_mkt_qty_cash_to_google_sheet(worksheet, ROW_BASE_POINTER_KI, g_row_stack_pointer_ki, buyable_cash_won_ki,
                                     **portfolio_input_ki)

    g_end_time = time.time()
    print(f'실행 시간: {g_end_time - g_start_time:.5f} 초\n')
    five_new_lines()

    """-------------------------------------------------------------------------------------------"""

    print('PortfolioCalculatorDuplicate.py----------------------------------------------------------')
    print()
    g_start_time = time.time()
    spreadsheet_url, _ = path_google_sheet()

    # Input
    book = auth_google_file('excel-editor-1.json', spreadsheet_url)
    existing_sheet_name = '*dashboard'
    to_copy_sheet_name = datetime.datetime.now().strftime('%Y%m%d')  # ex. 20240101

    # Process
    to_copy_sheet_name, existing_sheet = find_existing_sheet(existing_sheet_name, to_copy_sheet_name, book)

    # Save(.json)
    backup_exchange_rate(existing_sheet)

    # Duplicate(Google Sheet : *dashboard -> 20240101)
    put_excel_url_sheet_name_to_json_file(spreadsheet_url, to_copy_sheet_name)

    g_end_time = time.time()
    print(f'실행 시간: {g_end_time - g_start_time:.5f} 초\n')
    five_new_lines()

    """-------------------------------------------------------------------------------------------"""

    print('PortfolioCalculatorKI.py-----------------------------------------------------------------')
    g_start_time = time.time()
    check_token_expired()
    spreadsheet_url, sheet_name = path_google_sheet()

    # Input
    worksheet = auth_google_sheet('excel-editor-2.json', spreadsheet_url, sheet_name)
    buyable_cash_dollar_ki, portfolio_input_ki = get_portfolio_from_google_sheet_ki_1(worksheet, ROW_BASE_POINTER_KI,
                                                                                      g_row_stack_pointer_ki)
    worksheet = auth_google_sheet('excel-editor-3.json', spreadsheet_url, sheet_name)
    portfolio_input_ki = get_portfolio_from_google_sheet_ki_2(worksheet, ROW_BASE_POINTER_KI, g_row_stack_pointer_ki,
                                                              **portfolio_input_ki)

    # Process I
    portfolio_input_ki = get_market_from_ticker_book('ki', **portfolio_input_ki)
    portfolio_dict_ki = convert_portfolio_to_estimate('ki', **portfolio_input_ki)

    # Process II
    buyable_cash_dollar_ki, portfolio_dict_ki = estimate_portfolio_and_show_progress_ki(buyable_cash_dollar_ki,
                                                                                        **portfolio_dict_ki)

    # Save(.json)
    put_portfolio_to_json_file('ki', buyable_cash_dollar_ki, **portfolio_dict_ki)

    g_end_time = time.time()
    print(f'실행 시간: {g_end_time - g_start_time:.5f} 초\n')
    five_new_lines()

    """-------------------------------------------------------------------------------------------"""

    print('PortfolioCalculatorNH.py-----------------------------------------------------------------')
    g_start_time = time.time()
    check_token_expired()
    spreadsheet_url, sheet_name = path_google_sheet()

    # Input
    worksheet = auth_google_sheet('excel-editor-4.json', spreadsheet_url, sheet_name)
    buyable_cash_dollar_nh1, portfolio_input_nh1 = get_portfolio_from_google_sheet_nh('nh1', worksheet, ROW_BASE_POINTER_NH1,
                                                                                      ROW_STACK_POINTER_NH1)
    worksheet = auth_google_sheet('excel-editor-5.json', spreadsheet_url, sheet_name)
    buyable_cash_dollar_nh2, portfolio_input_nh2 = get_portfolio_from_google_sheet_nh('nh2', worksheet, ROW_BASE_POINTER_NH2,
                                                                                      ROW_STACK_POINTER_NH2)

    # Process I
    portfolio_input_nh1 = get_market_from_ticker_book('nh1', **portfolio_input_nh1)
    portfolio_input_nh2 = get_market_from_ticker_book('nh2', **portfolio_input_nh2)
    portfolio_dict_nh1 = convert_portfolio_to_estimate('nh1', **portfolio_input_nh1)
    portfolio_dict_nh2 = convert_portfolio_to_estimate('nh2', **portfolio_input_nh2)

    # Process II
    buyable_cash_dollar_nh1, portfolio_dict_nh1 = estimate_portfolio_and_show_progress_nh(buyable_cash_dollar_nh1,
                                                                                          **portfolio_dict_nh1)
    print('\n\n\n')
    buyable_cash_dollar_nh2, portfolio_dict_nh2 = estimate_portfolio_and_show_progress_nh(buyable_cash_dollar_nh2,
                                                                                          **portfolio_dict_nh2)

    # Save(.json)
    put_portfolio_to_json_file('nh1', buyable_cash_dollar_nh1, **portfolio_dict_nh1)
    put_portfolio_to_json_file('nh2', buyable_cash_dollar_nh2, **portfolio_dict_nh2)
    print()

    g_end_time = time.time()
    print(f'실행 시간: {g_end_time - g_start_time:.5f} 초\n')
    five_new_lines()

    """-------------------------------------------------------------------------------------------"""

    print('PortfolioCalculatorFillRed.py------------------------------------------------------------')
    g_start_time = time.time()
    check_token_expired()
    spreadsheet_url, sheet_name = path_google_sheet()

    # Load(.json)
    worksheet = auth_google_sheet('excel-editor-1.json', spreadsheet_url, sheet_name)
    portfolio_output_nh1 = open_json_file('./output/portfolio_output_nh1.json')
    portfolio_output_nh2 = open_json_file('./output/portfolio_output_nh2.json')
    portfolio_output_ki = open_json_file('./output/portfolio_output_ki.json')

    # Process
    check_portfolio_month('nh1', **portfolio_output_nh1)
    check_portfolio_month('nh2', **portfolio_output_nh2)
    check_portfolio_month('ki', **portfolio_output_ki)

    buyable_cash_dollar_nh1, portfolio_dict_nh1 = unpack_portfolio_data('nh1', **portfolio_output_nh1)
    buyable_cash_dollar_nh2, portfolio_dict_nh2 = unpack_portfolio_data('nh2', **portfolio_output_nh2)
    buyable_cash_dollar_ki, portfolio_dict_ki = unpack_portfolio_data('ki', **portfolio_output_ki)

    print_portfolio('nh1', buyable_cash_dollar_nh1, **portfolio_dict_nh1)
    print_portfolio('nh2', buyable_cash_dollar_nh2, **portfolio_dict_nh2)
    print_portfolio('ki', buyable_cash_dollar_ki, **portfolio_dict_ki)

    portfolio_dict_nh1 = {'BRK.B' if ticker == 'BRK/B' else ticker: list for ticker, list in portfolio_dict_nh1.items()}

    # Output(Google Sheet)
    put_target_qty_to_google_sheet(worksheet, 'nh1', ROW_BASE_POINTER_NH1, ROW_STACK_POINTER_NH1, **portfolio_dict_nh1)
    put_target_qty_to_google_sheet(worksheet, 'nh2', ROW_BASE_POINTER_NH2, ROW_STACK_POINTER_NH2, **portfolio_dict_nh2)
    put_target_qty_to_google_sheet(worksheet, 'ki', ROW_BASE_POINTER_KI, g_row_stack_pointer_ki, **portfolio_dict_ki)

    g_end_time = time.time()
    print(f'실행 시간: {g_end_time - g_start_time:.5f} 초')
    five_new_lines()


main()
