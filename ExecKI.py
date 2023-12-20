from PortfolioRebalancingCore import check_token_expired
from FuncCommon import path_google_sheet
from FuncCommon import auth_google_sheet
from FuncCommon import get_market_from_ticker_book
from FuncCommon import convert_portfolio_to_estimate
from FuncCommon import put_portfolio_to_json_file
from FuncPurpleKI import get_portfolio_from_google_sheet
from FuncRedKI import get_portfolio_from_google_sheet_1
from FuncRedKI import get_portfolio_from_google_sheet_2
from FuncRedKI import estimate_portfolio_and_show_progress_ki
import time


ROW_BASE_POINTER = 26
g_row_stack_pointer = 0


"""FuncRedKI.py-----------------------------------------------------------------------------"""

g_start_time = time.time()
check_token_expired()
spreadsheet_url, sheet_name = path_google_sheet()

# (Get g_row_stack_pointer)
worksheet1 = auth_google_sheet('excel-editor-3.json', spreadsheet_url, sheet_name)
g_row_stack_pointer, _, _ = get_portfolio_from_google_sheet(worksheet1, ROW_BASE_POINTER)

# Input
worksheet2 = auth_google_sheet('excel-editor-4.json', spreadsheet_url, sheet_name)
buyable_cash_dollar_ki, portfolio_input_ki = get_portfolio_from_google_sheet_1(worksheet2, ROW_BASE_POINTER, g_row_stack_pointer)
worksheet3 = auth_google_sheet('excel-editor-5.json', spreadsheet_url, sheet_name)
portfolio_input_ki = get_portfolio_from_google_sheet_2(worksheet3, ROW_BASE_POINTER, g_row_stack_pointer, **portfolio_input_ki)

# Process I
portfolio_input_ki = get_market_from_ticker_book('ki', **portfolio_input_ki)
portfolio_dict_ki = convert_portfolio_to_estimate('ki', **portfolio_input_ki)

# Process II
buyable_cash_dollar_ki, portfolio_dict_ki = estimate_portfolio_and_show_progress_ki(buyable_cash_dollar_ki, **portfolio_dict_ki)

# Output
put_portfolio_to_json_file('ki', buyable_cash_dollar_ki, **portfolio_dict_ki)

"""실행 시간"""
g_end_time = time.time()
print(f"실행 시간: {g_end_time - g_start_time:.5f} 초\n")
