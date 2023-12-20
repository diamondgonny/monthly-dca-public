from FuncCommon import path_google_sheet
from FuncCommon import auth_google_sheet
from PortfolioRebalancingCore import check_token_expired
from PortfolioRebalancingPrint import show_dashboard
import datetime
import json
import time


g_start_time = time.time()
ROW_BASE_POINTER_NH1 = 2
ROW_STACK_POINTER_NH1 = 8
ROW_BASE_POINTER_NH2 = 12
ROW_STACK_POINTER_NH2 = 21
ROW_BASE_POINTER_KI = 26
g_row_stack_pointer_ki = 0


def open_json_file(filepath: str):
    with open(filepath, 'r', encoding='UTF-8') as f:
        dictname = json.load(f)
        return dictname


def check_portfolio_month(pf_code: str, **portfolio_output):
    update_date_str = portfolio_output[f'update_date_{pf_code}']
    update_date = datetime.datetime.strptime(update_date_str, "%Y-%m-%d %H:%M:%S")
    current_date = datetime.datetime.now()
    is_same_month = (update_date.year, update_date.month) == (current_date.year, current_date.month)
    if not is_same_month:
        raise Exception(f'이번 달 자료가 아닙니다. portfolio_output_{pf_code} 자료를 업데이트하고 다시 시도하세요.')


def unpack_portfolio_data(pf_code: str, **portfolio_output):
    buyable_cash_dollar = portfolio_output[f'buyable_cash_dollar_{pf_code}']
    portfolio_dict = portfolio_output[f'portfolio_dict_{pf_code}']
    return buyable_cash_dollar, portfolio_dict


def generate_total_etfs_and_to_order_etfs(**portfolio_dict):
    total_etfs_dollar = 0
    to_order_etfs_dollar = 0
    for ticker in portfolio_dict:
        total_etfs_dollar += portfolio_dict[ticker][4]
        to_order_etfs_dollar += portfolio_dict[ticker][12]
    return total_etfs_dollar, to_order_etfs_dollar


def print_portfolio(pf_code: str, buyable_cash_dollar: float, **portfolio_dict):
    total_etfs_dollar, to_order_etfs_dollar = generate_total_etfs_and_to_order_etfs(**portfolio_dict)
    print(f"portfolio_output_{pf_code})", end=" ")
    show_dashboard(total_etfs_dollar, buyable_cash_dollar, to_order_etfs_dollar, False, **portfolio_dict)


def estimate_row_stack_pointer_ki(row_base_pointer: int):
    global g_row_stack_pointer_ki
    row_pointer = row_base_pointer
    while True:
        ticker = worksheet.cell(row_pointer, 1).value
        if ticker == "(buyable_cash)":
            g_row_stack_pointer_ki = row_pointer
            print(f"g_row_stack_pointer_ki : {g_row_stack_pointer_ki}\n")
            break
        row_pointer += 1


def put_target_qty_to_google_sheet(pf_code: str, row_base_pointer: int, row_stack_pointer: int, **portfolio_dict):
    update_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row_pointer = row_base_pointer
    print("Loading...")

    for ticker_from, list in portfolio_dict.items():
        ticker_to = worksheet.cell(row_pointer, 1).value
        if row_pointer >= row_stack_pointer:
            raise Exception(f'Sheet({row_stack_pointer - row_base_pointer}), '
                            f'JSON({row_pointer - row_base_pointer + 1} 이상): 저장된 포트폴리오({pf_code})의 종목 갯수 불일치')
        if ticker_from != ticker_to:
            raise Exception(f'JSON({ticker_from}), Sheet({ticker_to}) : 저장된 포트폴리오({pf_code})의 종목 순서 불일치')
        target_qty = list[7]
        worksheet.update_cell(row_pointer, 11, target_qty)
        row_pointer += 1
        print(ticker_from, ticker_to)
    if row_pointer != row_stack_pointer:
        raise Exception(f'Sheet({row_stack_pointer - row_base_pointer}), JSON({row_pointer - row_base_pointer})'
                        f': 저장된 포트폴리오({pf_code})의 종목 갯수 불일치')
    worksheet.update_cell(2, 18, update_date)
    print(f"Updated target qty of 'portfolio_dict_{pf_code}' to Google Sheet.\n")


"""-----------------------------------------------------------------------------------------"""

check_token_expired()
spreadsheet_url, sheet_name = path_google_sheet()

worksheet = auth_google_sheet("excel-editor-1.json", spreadsheet_url, sheet_name)
portfolio_output_nh1 = open_json_file('./output/portfolio_output_nh1.json')
portfolio_output_nh2 = open_json_file('./output/portfolio_output_nh2.json')
portfolio_output_ki = open_json_file('./output/portfolio_output_ki.json')

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

estimate_row_stack_pointer_ki(ROW_BASE_POINTER_KI)
put_target_qty_to_google_sheet('nh1', ROW_BASE_POINTER_NH1, ROW_STACK_POINTER_NH1, **portfolio_dict_nh1)
put_target_qty_to_google_sheet('nh2', ROW_BASE_POINTER_NH2, ROW_STACK_POINTER_NH2, **portfolio_dict_nh2)
put_target_qty_to_google_sheet('ki', ROW_BASE_POINTER_KI, g_row_stack_pointer_ki, **portfolio_dict_ki)

"""실행 시간"""
g_end_time = time.time()
print(f"실행 시간: {g_end_time - g_start_time:.5f} 초")
