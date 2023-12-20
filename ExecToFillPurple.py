from PortfolioRebalancingCore import check_token_expired
from FuncCommon import path_google_sheet
from FuncCommon import auth_google_sheet
from FuncCommon import get_market_from_ticker_book
from FuncPurpleKI import get_portfolio_from_google_sheet
from FuncPurpleKI import get_qty_from_kis_developers
from FuncPurpleKI import get_buyable_cash_from_kis_developers
from FuncPurpleKI import put_mkt_qty_cash_to_google_sheet
import time


ROW_BASE_POINTER = 26
g_row_stack_pointer = 0


"""FuncPurpleKI.py--------------------------------------------------------------------------"""

g_start_time = time.time()
check_token_expired()
spreadsheet_url, sheet_name = path_google_sheet()

# Input
worksheet1 = auth_google_sheet('excel-editor-3.json', spreadsheet_url, sheet_name)
g_row_stack_pointer, buyable_cash_won_ki, portfolio_input_ki = get_portfolio_from_google_sheet(worksheet1, ROW_BASE_POINTER)


# Process
portfolio_input_ki = get_market_from_ticker_book('ki', **portfolio_input_ki)
# portfolio_input_ki = get_qty_from_kis_developers(**portfolio_input_ki)  # 보라색 칸의 현재수량을 받지 않는다고 가정
# buyable_cash_won_ki = get_buyable_cash_from_kis_developers()  # "

# Output
put_mkt_qty_cash_to_google_sheet(worksheet1, ROW_BASE_POINTER, g_row_stack_pointer, buyable_cash_won_ki, **portfolio_input_ki)
print()

"""실행 시간"""
g_end_time = time.time()
print(f"실행 시간: {g_end_time - g_start_time:.5f} 초\n")
g_start_time = time.time()
