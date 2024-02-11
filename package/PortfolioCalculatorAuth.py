from oauth2client.service_account import ServiceAccountCredentials
import os
import gspread
import json


def open_json_file(filepath: str):
    with open(filepath, 'r', encoding='UTF-8') as f:
        dictname = json.load(f)

    return dictname


def path_google_sheet():
    with open('config/google-sheet.json', 'r', encoding='UTF-8') as f:
        _gsheet = json.load(f)
    spreadsheet_url = _gsheet['spreadsheet_url']

    return spreadsheet_url


def auth_google_file(filename: str, spreadsheet_url: str):
    # Google Sheet API는 분당 60건 API 호출 가능
    json_file_name = os.getcwd() + '/config/' + filename  # 서비스계정의 KEY. JSON Key File 경로
    scope = ['https://spreadsheets.google.com/feeds']  # Google API 요청 시 필요한 권한 유형
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_name, scope)  # 사용자 계정의 자격증명
    gc = gspread.authorize(credentials)  # Google API에 로그인
    book = gc.open_by_url(spreadsheet_url)  # 스프레드시트 열기
    print(f'Login : {filename[0:-5]}')

    return book


def auth_google_sheet(filename: str, spreadsheet_url: str, sheet_name: str):
    book = auth_google_file(filename, spreadsheet_url)
    worksheet = book.worksheet(sheet_name)  # 스프레드시트에 들어있는 워크시트 선택

    return worksheet
