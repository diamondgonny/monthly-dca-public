from crontab import CronTab
from datetime import date
import calendar
import datetime
import difflib


# Define public holidays for 2024 in the US
public_holidays_2024 = [
    "2024-01-01",  # New Year's Day
    "2024-01-15",  # Martin Luther King Jr. Day
    "2024-02-19",  # Washington's Birthday
    "2024-03-29",  # Good Friday
    "2024-05-27",  # Memorial Day
    "2024-06-19",  # Juneteenth National Independence Day
    "2024-07-04",  # Independence Day
    "2024-09-02",  # Labor Day
    "2024-11-28",  # Thanksgiving Day
    "2024-12-25",  # Christmas Day
]


def find_first_business_day_of_the_month(year, holidays):
    first_business_day_of_the_month = []
    for month in range(1, 13):
        day = date(year, month, 1)
        while True:
            if day.weekday() < 5 and day.strftime('%Y-%m-%d') not in holidays:
                first_business_day_of_the_month.append(day)
                break
            day += datetime.timedelta(days=1)
    return first_business_day_of_the_month


def find_two_business_days_later(dates, holidays):
    two_business_days_later_list = []
    for day in dates:
        # Start counting from the next day : +1 -> +2 -> (+3) -> +2
        next_day = day + datetime.timedelta(days=1)
        business_days_counted = 0
        while business_days_counted < 2:
            if next_day.weekday() < 5 and next_day.strftime('%Y-%m-%d') not in holidays:
                business_days_counted += 1
            next_day += datetime.timedelta(days=1)
        two_business_days_later_list.append(next_day - datetime.timedelta(days=1))
    return two_business_days_later_list


def get_current_month_str():
    now = datetime.datetime.now()
    return now.strftime('%m')


def get_last_day_of_this_month():
    today = datetime.date.today()
    year, month = today.year, today.month
    last_day = calendar.monthrange(year, month)[1]
    return last_day


def color_diff(diff):
    for line in diff:
        if line.startswith('+'):
            yield "\033[32m" + line + "\033[0m"  # 녹색
        elif line.startswith('-'):
            yield "\033[31m" + line + "\033[0m"  # 빨간색
        else:
            yield line


def ask_user_to_activate(trade_date_of_this_month: str, diff_str: str, new_cron_jobs: str):
    is_to_activate = False
    if diff_str:
        print('Crontab 변경사항)', trade_date_of_this_month)
        print(diff_str, '\n')
        signal = input('위의 내용대로 Crontab에 입력됩니다. 계속 진행하시겠습니까? (Y/N) : ')
        if signal.lower() == 'y':
            is_to_activate = True
        else:
            print(f'{signal} : Canceled to update crontab.')
    else:
        print('Crontab 변경사항)', trade_date_of_this_month)
        print(new_cron_jobs, '\n')
        print('No changes in crontab.')

    return is_to_activate


def crontab_message_generator(trade_date_of_this_month: str, day: int, month: int):
    year = datetime.date.today().year
    last_day_of_this_month = get_last_day_of_this_month()
    next_day = day + 1
    if next_day > last_day_of_this_month:
        raise Exception(f'{year}년 {month}월 {next_day}일? 존재하지 않는 날짜 입니다. 다시 시도하세요.')

    my_cron = CronTab(user=True)
    existing_cron_jobs = '\n'.join(str(job) for job in my_cron)
    existing_cron_jobs = existing_cron_jobs.replace('\\\\', '\\')  # escape_sequence

    with open('./config/backup-crontab-generator-info.txt', 'r') as file:
        new_cron_jobs = file.read()
    new_cron_jobs = new_cron_jobs.format(day=day, next_day=next_day, month=month)

    diff = difflib.unified_diff(existing_cron_jobs.splitlines(), new_cron_jobs.splitlines(), fromfile='current', tofile='new', lineterm='')
    colored_diff = color_diff(diff)
    diff_str = '\n'.join(colored_diff)

    is_to_activate = ask_user_to_activate(trade_date_of_this_month, diff_str, new_cron_jobs)
    if not is_to_activate:
        exit()

    # 기존 crontab을 새로운 설정으로 변경
    my_cron.remove_all()
    for line in new_cron_jobs.strip().splitlines():
        parts = line.split(None, 5)
        schedule = ' '.join(parts[:5])
        command = parts[5]
        command = command.replace("\%", "%")  # escape_sequence
        job = my_cron.new(command=command)
        job.setall(schedule)
        my_cron.write()
    print("Crontab updated successfully.")


def main():
    first_business_day_of_the_month = find_first_business_day_of_the_month(2024, public_holidays_2024)
    third_business_day_of_the_month_list = find_two_business_days_later(first_business_day_of_the_month,
                                                                        public_holidays_2024)
    third_business_day_of_the_month_str_list = [third_business_day.strftime('%Y-%m-%d, %A')
                                                for third_business_day in third_business_day_of_the_month_list]

    print('*** 2024 Trade Day List ***')
    for third_business_day_of_the_month in third_business_day_of_the_month_str_list:
        print(third_business_day_of_the_month)
    print()

    third_business_day_of_this_month = ''
    current_month_str = get_current_month_str()
    if current_month_str in third_business_day_of_the_month_str_list[int(current_month_str) - 1][5:7]:
        third_business_day_of_this_month = third_business_day_of_the_month_str_list[int(current_month_str) - 1]
    current_day_str = third_business_day_of_this_month[8:10]
    day = int(current_day_str)
    month = int(current_month_str)

    crontab_message_generator(third_business_day_of_this_month, day, month)


main()
