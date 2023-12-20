from gspread import Spreadsheet
from gspread import Worksheet
from FuncCommon import path_google_sheet
from FuncCommon import auth_google_file
import datetime
import json


def check_name_conflict(existing_sheet_name: str, to_copy_sheet_name_check: str, book: Spreadsheet, to_copy_sheet: Worksheet):
    # 가령 20240101이 이미 존재한다면, 20240101+을 새로 만들어 대시보드를 복사함
    today_record_already_exists = False
    for worksheet in book.worksheets():
        if worksheet.title == to_copy_sheet_name_check:
            today_record_already_exists = True
            break
    if today_record_already_exists:  # recursive
        print(f"A sheet with the name '{to_copy_sheet_name_check}' already exists.")
        to_copy_sheet_name_check = check_name_conflict(existing_sheet_name, to_copy_sheet_name_check + '+', book, to_copy_sheet)
    else:
        to_copy_sheet.update_title(to_copy_sheet_name_check)
        print(f"Sheet '{existing_sheet_name}' copied and renamed successfully as '{to_copy_sheet_name_check}'")

    return to_copy_sheet_name_check


def find_existing_sheet(existing_sheet_name: str, to_copy_sheet_name: str, book: Spreadsheet):
    existing_sheet = None
    for sheet in book.worksheets():
        if sheet.title == existing_sheet_name:
            existing_sheet = sheet
            break
    if existing_sheet:
        existing_sheet_id = existing_sheet.id
        to_copy_sheet = book.duplicate_sheet(existing_sheet_id)
        to_copy_sheet_name = check_name_conflict(existing_sheet_name, to_copy_sheet_name, book, to_copy_sheet)
    else:
        raise Exception(f"Sheet '{existing_sheet_name}' not found in the spreadsheet.")

    return to_copy_sheet_name, to_copy_sheet


def put_excel_url_sheet_name_to_json_file(spreadsheet_url: str, to_copy_sheet_name: str):
    excel_url_sheet = {
        'spreadsheet_url': spreadsheet_url,
        'sheet_name': to_copy_sheet_name
    }
    with open('./config/excel-url-sheet-name.json', 'w', encoding='UTF-8') as f:
        json.dump(excel_url_sheet, f, indent=2, sort_keys=False)
        print(f'./config/excel-url-sheet-name.json에 복사된 시트({to_copy_sheet_name})의 경로를 남겼습니다.')


def backup_exchange_rate(to_copy_sheet: Worksheet):
    # 간혹 float 타입의 환율 대신, 문자열인 '로딩 중...'을 입력받아 생기는 문제를 보완하고자 backup
    update_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    exchange_rate = float(to_copy_sheet.cell(2, 19).value.lstrip('₩').replace(',', ''))
    exchange_rate_dict = {
        'update_date': update_date,
        'exchange_rate': exchange_rate
    }
    with open(f'./config/backup-exchange-rate.json', 'w', encoding='UTF-8') as f:
        json.dump(exchange_rate_dict, f, indent=2, sort_keys=False)
        print(f'./config/backup-exchange-rate.json에 환율 백업 데이터를 남겼습니다.')


"""-----------------------------------------------------------------------------------------"""

spreadsheet_url, _ = path_google_sheet()

# Input
book = auth_google_file("excel-editor-5.json", spreadsheet_url)
existing_sheet_name = '*dashboard'
to_copy_sheet_name = datetime.datetime.now().strftime("%Y%m%d")  # ex. 20240101

# Process
to_copy_sheet_name, to_copy_sheet = find_existing_sheet(existing_sheet_name, to_copy_sheet_name, book)

# Output
backup_exchange_rate(to_copy_sheet)
put_excel_url_sheet_name_to_json_file(spreadsheet_url, to_copy_sheet_name)
