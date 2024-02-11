from gspread import Spreadsheet
from gspread import Worksheet


def check_name_conflict_recursive(existing_sheet_name: str, to_copy_sheet_name: str, book: Spreadsheet, to_copy_sheet: Worksheet):
    # 가령 20240101이 이미 존재한다면, 20240101 뒤에 '+'를 새로 덧붙인 이름을 만들어주는 '재귀함수'임 (e.g. 20240101++이 존재하면 20240101+++)
    today_record_already_exists = False
    for worksheet in book.worksheets():
        if worksheet.title == to_copy_sheet_name:
            today_record_already_exists = True
            break
    if today_record_already_exists:
        print(f"A sheet with the name '{to_copy_sheet_name}' already exists.")
        to_copy_sheet_name = check_name_conflict_recursive(existing_sheet_name, to_copy_sheet_name + '+', book, to_copy_sheet)
    else:
        to_copy_sheet.update_title(to_copy_sheet_name)
        print(f"Sheet '{existing_sheet_name}' copied and renamed successfully as '{to_copy_sheet_name}'.\n")

    return to_copy_sheet_name


def find_existing_sheet_and_duplicate(existing_sheet_name: str, to_copy_sheet_name: str, book: Spreadsheet):
    # 말 그대로 기존의 스프레드시트(existing_sheet_name)를 찾아서 새로운 스프레드시트(to_copy_sheet_name)로 복사해주는 함수
    existing_sheet = None
    for sheet in book.worksheets():
        if sheet.title == existing_sheet_name:
            existing_sheet = sheet
            break
    if existing_sheet:
        existing_sheet_id = existing_sheet.id
        to_copy_sheet = book.duplicate_sheet(existing_sheet_id, insert_sheet_index=4)
        to_copy_sheet_name = check_name_conflict_recursive(existing_sheet_name, to_copy_sheet_name, book, to_copy_sheet)
    else:
        raise Exception(f"Sheet '{existing_sheet_name}' not found in the spreadsheet.")

    return to_copy_sheet_name
