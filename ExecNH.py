from PortfolioRebalancingCore import check_token_expired
from FuncCommon import path_google_sheet
from FuncCommon import auth_google_sheet
from FuncCommon import get_market_from_ticker_book
from FuncCommon import convert_portfolio_to_estimate
from FuncCommon import put_portfolio_to_json_file
from FuncRedNH import get_portfolio_from_google_sheet
from FuncRedNH import estimate_portfolio_and_show_progress_nh
import time


ROW_BASE_POINTER_1 = 2
ROW_STACK_POINTER_1 = 8
ROW_BASE_POINTER_2 = 12
ROW_STACK_POINTER_2 = 21


"""-----------------------------------------------------------------------------------------"""

g_start_time = time.time()
check_token_expired()
spreadsheet_url, sheet_name = path_google_sheet()

# Input
worksheet = auth_google_sheet('excel-editor-1.json', spreadsheet_url, sheet_name)
buyable_cash_dollar_nh1, portfolio_input_nh1 = get_portfolio_from_google_sheet('nh1', worksheet, ROW_BASE_POINTER_1, ROW_STACK_POINTER_1)
worksheet = auth_google_sheet('excel-editor-2.json', spreadsheet_url, sheet_name)
buyable_cash_dollar_nh2, portfolio_input_nh2 = get_portfolio_from_google_sheet('nh2', worksheet, ROW_BASE_POINTER_2, ROW_STACK_POINTER_2)

# Process I
portfolio_input_nh1 = get_market_from_ticker_book('nh1', **portfolio_input_nh1)
portfolio_input_nh2 = get_market_from_ticker_book('nh2', **portfolio_input_nh2)
portfolio_dict_nh1 = convert_portfolio_to_estimate('nh1', **portfolio_input_nh1)
portfolio_dict_nh2 = convert_portfolio_to_estimate('nh2', **portfolio_input_nh2)

# Process II
buyable_cash_dollar_nh1, portfolio_dict_nh1 = estimate_portfolio_and_show_progress_nh(buyable_cash_dollar_nh1, **portfolio_dict_nh1)
for i in range(0, 7):
    print()
buyable_cash_dollar_nh2, portfolio_dict_nh2 = estimate_portfolio_and_show_progress_nh(buyable_cash_dollar_nh2, **portfolio_dict_nh2)

# Output
put_portfolio_to_json_file('nh1', buyable_cash_dollar_nh1, **portfolio_dict_nh1)
put_portfolio_to_json_file('nh2', buyable_cash_dollar_nh2, **portfolio_dict_nh2)
print()

"""실행 시간"""
g_end_time = time.time()
print(f"실행 시간: {g_end_time - g_start_time:.5f} 초\n")
