from oauth2client.service_account import ServiceAccountCredentials
import openpyxl
import os
import gspread
import datetime
import json


def path_google_sheet():
    with open('config/excel-url-sheet-name.json', 'r', encoding='UTF-8') as f:
        _gsheet = json.load(f)
    spreadsheet_url = _gsheet['spreadsheet_url']
    sheet_name = _gsheet['sheet_name']

    return spreadsheet_url, sheet_name


def auth_google_file(filename: str, spreadsheet_url: str):
    # Google Sheet API는 분당 60건 API 호출 가능
    json_file_name = os.getcwd() + "/config/" + filename  # 서비스계정의 KEY. JSON Key File 경로
    scope = ['https://spreadsheets.google.com/feeds']  # Google API 요청 시 필요한 권한 유형
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_name, scope)  # 사용자 계정의 자격증명
    gc = gspread.authorize(credentials)  # Google API에 로그인
    book = gc.open_by_url(spreadsheet_url)  # 스프레드 시트 Open
    print(f"Login : {filename[0:-5]}\n")

    return book


def auth_google_sheet(filename: str, spreadsheet_url: str, sheet_name: str):
    book = auth_google_file(filename, spreadsheet_url)
    worksheet = book.worksheet(sheet_name)  # 스프레드 시트의 워크시트 선택

    return worksheet


def get_market_from_ticker_book(pf_code: str, **portfolio_dict):
    xlsx_file_name = os.getcwd() + "/overseas_stock_code/overseas_stock_code(all).xlsx"  # 엑셀파일 열기, 엑셀 파일의 첫번째 시트 추출하기
    book_xl = openpyxl.load_workbook(xlsx_file_name)
    worksheet_xl = book_xl.worksheets[0]
    print("Loading...")

    for ticker, list in portfolio_dict.items():
        for cell in worksheet_xl['E']:
            if ticker == cell.value:
                market: str = worksheet_xl.cell(row=cell.row, column=cell.column - 2).value
                if market == 'AMS':
                    market = 'AMEX'
                elif market == 'NAS':
                    market = 'NASD'
                elif market == 'NYS':
                    market = 'NYSE'
                list[1] = market
                break
    print(f"Received market data from Ticker Book to 'portfolio_input_{pf_code}'.\n")

    return portfolio_dict


def convert_portfolio_to_estimate(pf_code: str, **portfolio_input):
    """보유종목 : [자산분류, 시장분류, 단가($), 현재보유량(주), 현재평가금액($), 현재배분율[R](%), (현재배분율[I](%)), 목표보유량(주),
                목표평가금액($), 목표배분율[R](%), (목표배분율[I](%)), 목표매매량(주), 예상매매금액($), 괴리율(%), 매수1호가($), 매도1호가($)]"""
    portfolio_dict = {}
    print("Loading...")

    for ticker, input_list in portfolio_input.items():
        """input_list = [asset_class, market, current_qty, current_pct, target_pct]"""
        list = [input_list[0], input_list[1], 0, input_list[2], 0, 0, input_list[3], 0, 0, 0, input_list[4], 0, 0, 0, 0, 0]
        portfolio_dict[ticker] = list
    print(f"Converted 'portfolio_dict_{pf_code}' to estimate in Calculator.\n")

    return portfolio_dict


def put_portfolio_to_json_file(pf_code: str, buyable_cash_dollar: float, **portfolio_dict):
    update_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    portfolio_output = {
        f'update_date_{pf_code}': update_date,
        f'buyable_cash_dollar_{pf_code}': buyable_cash_dollar,
        f'portfolio_dict_{pf_code}': portfolio_dict
    }
    with open(f'./output/portfolio_output_{pf_code}.json', 'w', encoding='UTF-8') as f:
        json.dump(portfolio_output, f, indent=2, sort_keys=False)
        print(f"portfolio_output_{pf_code}.json에 결과지를 남겼습니다.")
