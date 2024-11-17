import requests
import json
import time
import datetime
from pytz import timezone

# 프로그램 처음 실행할 때 kis-developer.json 접근토큰 설정:
# "access_token", "access_token_expired"의 value는 공란("")으로 함
with open('config/kis-developer.json', 'r', encoding='UTF-8') as f:
    _cfg = json.load(f)  # parse

APP_KEY = _cfg['app_key']
APP_SECRET = _cfg['app_secret']
CANO = _cfg['cano']
ACNT_PRDT_CD = _cfg['acnt_prdt_cd']
DISCORD_WEBHOOK_URL = _cfg['discord_webhook_url']
URL_BASE = _cfg['url_base']
g_access_token = _cfg['access_token']
g_access_token_expired = _cfg['access_token_expired']

# 매매주문시 몇프로를 무르고 주문할 것인가 (ex. 0.2%)
SELL_ORDER_DISADVANTAGE_RATE_PCT = 1.0
BUY_ORDER_DISADVANTAGE_RATE_PCT = 0.2
# 거래수수료 (ex. 0.09%)
TRANSACTION_FEE_RATE_PCT = 0.09


def my_print(to_print: bool, message, end='\n'):
    if to_print:
        print(message, end=end)


def get_access_token():
    """토큰 발급"""
    headers = {
        "content-type": "application/json"
    }
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET
    }
    PATH = "oauth2/tokenP"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    access_token = res.json()['access_token']
    access_token_expired = res.json()['access_token_token_expired']
    return access_token, access_token_expired


def check_token_expired():
    """토큰 만료 검사 후 토큰 재발급"""
    global g_access_token_expired
    print('현재 시각: {}, 토큰만료 시각: {}'.format(time.strftime('%Y-%m-%d %H:%M:%S'), g_access_token_expired))
    if time.strftime('%Y-%m-%d %H:%M:%S') >= g_access_token_expired:
        print('접근토큰이 없거나 만료되었으므로, 새로 발급받겠습니다...')
        reissue_token_core()
    else:
        print('접근토큰이 유효하므로, 바로 진행하겠습니다.\n')


def reissue_token_expired():
    """토큰 만료 검사 없이 토큰 재발급"""
    global g_access_token_expired
    print('현재 시각: {}, 토큰만료 시각: {}'.format(time.strftime('%Y-%m-%d %H:%M:%S'), g_access_token_expired))
    print('접근토큰을 새로 발급받겠습니다...')
    reissue_token_core()


def reissue_token_core():
    """토큰 재발급 로직"""
    global g_access_token
    global g_access_token_expired
    try:
        g_access_token, g_access_token_expired = get_access_token()
        _cfg.update({'access_token': g_access_token, 'access_token_expired': g_access_token_expired})
        with open('config/kis-developer.json', 'w', encoding='UTF-8') as fwrite:
            json.dump(_cfg, fwrite, indent=2, sort_keys=False)  # serialize
        print('접근토큰 발급 완료.\n')
        time.sleep(1)
    except Exception as e:
        print(f'[접근토큰 발급 오류]{e}')
        time.sleep(1)


def hashkey(datas):
    """암호화"""
    PATH = "uapi/hashkey"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        "content-Type": "application/json",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET
    }
    res = requests.post(URL, headers=headers, data=json.dumps(datas))
    hash_key = res.json()['HASH']
    return hash_key


def send_message(msg):
    """디스코드 메세지 전송"""
    message = {"content": f"{str(msg)}"}
    requests.post(DISCORD_WEBHOOK_URL, data=message)
    print(message)


def get_portfolio_mkt_qty():
    """포트폴리오 시장분류 및 보유수량 조회"""
    PATH = "uapi/overseas-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {g_access_token}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "JTTT3012R",
        "custtype": "P"
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": "NASD",
        "TR_CRCY_CD": "USD",
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    portfolio_mkt_qty = res.json()['output1']
    portfolio_mkt_qty_dict = {}
    # send_message(f'====보유수량====')
    for pack in portfolio_mkt_qty:
        if int(pack['ovrs_cblc_qty']) > 0:
            portfolio_mkt_qty_list = [pack['ovrs_excg_cd'], int(pack['ovrs_cblc_qty'])]
            portfolio_mkt_qty_dict[pack['ovrs_pdno']] = portfolio_mkt_qty_list
            # send_message(f"{pack['ovrs_item_name']}({pack['ovrs_pdno']}): {pack['ovrs_cblc_qty']}주")
    # send_message(f'=====================')
    return portfolio_mkt_qty_dict


def get_total_etfs_evlu_dollar():
    """평가금액 리스트 조회"""
    PATH = "uapi/overseas-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {g_access_token}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "JTTT3012R",
        "custtype": "P"
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": "NASD",
        "TR_CRCY_CD": "USD",
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    evaluation = res.json()['output2']
    evaluation_total_profit_loss = evaluation['ovrs_tot_pfls']
    evaluation_total_price = evaluation['tot_evlu_pfls_amt']
    return float(evaluation_total_profit_loss), float(evaluation_total_price)


def get_buyable_cash_dollar_and_exchange_rate():
    """주문 가능 현금(달러) 및 환율(원/달러) 조회"""
    PATH = "uapi/overseas-stock/v1/trading/inquire-psamount"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {g_access_token}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "JTTT3007R"
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": "NASD",
        "OVRS_ORD_UNPR": "0",
        "ITEM_CD": "TSLA"
    }
    res = requests.get(URL, headers=headers, params=params)
    cash = res.json()['output']['frcr_ord_psbl_amt1']
    exrt = res.json()['output']['exrt']
    return float(cash), float(exrt)


def get_asset_info_won():
    """해외자산 종합조회(원화)"""
    PATH = "uapi/overseas-stock/v1/trading/inquire-present-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {g_access_token}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "CTRP6504R"
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "WCRC_FRCR_DVSN_CD": "01",  # 원화외화 구분코드(원화)
        "NATN_CD": "840",
        "TR_MKET_CD": "00",
        "INQR_DVSN_CD": "00"
    }
    res = requests.get(URL, headers=headers, params=params)
    balance = res.json()['output3']
    total_etfs_won = balance['evlu_amt_smtl']  # 해외etf 평가금액(원화)
    korean_cash_won = balance['tot_dncl_amt']  # 원화예수금(원화)
    us_cash_won = balance['frcr_evlu_tota']  # 달러예수금(원화)
    unsettled_buy_amount_etfs_won = balance['ustl_buy_amt_smtl']  # 해외etf 미결제매수금액 합계(원화)
    unsettled_sell_amount_etfs_won = balance['ustl_sll_amt_smtl']  # 해외etf 미결제매도금액 합계(원화)
    total_assets_won = balance['tot_asst_amt']  # 총자산 = 해외etf평가금액 + 원화예수금 + 해외예수금(원화)
    return int(total_etfs_won), int(korean_cash_won), int(us_cash_won), int(total_assets_won), int(
        unsettled_buy_amount_etfs_won), int(unsettled_sell_amount_etfs_won)


def get_current_price(ticker='AAPL', market='NASD'):
    """현재가 조회"""
    if market == 'AMEX':  # API의 비일관적인 시장분류코드로 인한 코드변환
        market = 'AMS'
    elif market == 'NASD':
        market = 'NAS'
    elif market == 'NYSE':
        market = 'NYS'
    PATH = "uapi/overseas-price/v1/quotations/price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {g_access_token}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "HHDFS00000300"
    }
    params = {
        "AUTH": "",
        "SYMB": ticker,
        "EXCD": market
    }
    res = requests.get(URL, headers=headers, params=params)
    current_price = res.json()['output']['last']
    return float(current_price)


def get_bid_ask_price(ticker='AAPL', market='NASD'):
    """매수1호가, 매도1호가 조회"""
    if market == 'AMEX':  # API의 비일관적인 시장분류코드로 인한 코드변환
        market = 'AMS'
    elif market == 'NASD':
        market = 'NAS'
    elif market == 'NYSE':
        market = 'NYS'
    PATH = "/uapi/overseas-price/v1/quotations/dailyprice"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {g_access_token}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "HHDFS76240000"
    }
    params = {
        "AUTH": "",
        "SYMB": ticker,
        "EXCD": market,
        "GUBN": "0",
        "BYMD": "",
        "MODP": "0"
    }
    res = requests.get(URL, headers=headers, params=params)
    bid = res.json()['output2'][0]['pbid']  # 매수1호가
    ask = res.json()['output2'][0]['pask']  # 매도1호가
    return float(bid), float(ask)


def get_inquire_nccs(to_print_progress: bool):
    """(진행중인 주문의) 미체결내역 조회    <- 당일 정규장 운영시간 내에만 API 호출 가능"""
    PATH = "uapi/overseas-stock/v1/trading/inquire-nccs"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {g_access_token}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "JTTT3018R",
        "custtype": "P"
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": "NASD",
        "SORT_SQN": "DS",
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    today_pending_order = res.json()['output']
    today_pending_order_dict = {}
    for pack in today_pending_order:
        sell_or_buy: str = 'sell' if pack['sll_buy_dvsn_cd'] == '01' else 'buy'
        today_pending_order_list = [int(pack['ft_ord_qty']), int(pack['ft_ccld_qty']), int(pack['nccs_qty']), sell_or_buy]
        if pack['pdno'] in today_pending_order_dict:
            today_pending_order_dict[pack['pdno']][0] += int(pack['ft_ord_qty'])
            today_pending_order_dict[pack['pdno']][1] += int(pack['ft_ccld_qty'])
            today_pending_order_dict[pack['pdno']][2] += int(pack['nccs_qty'])
            my_print(to_print_progress, f"+ '{pack['pdno']}': {today_pending_order_list}")
            my_print(to_print_progress, today_pending_order_dict)
        else:
            today_pending_order_dict[pack['pdno']] = today_pending_order_list
            # 같은 종목에서의 매도, 매수는 동시에 pending order 할 수 없음 (자전거래 규제)
    return today_pending_order_dict


def get_inquire_ccnl_order(to_print_progress: bool):
    """체결내역 조회"""
    t_now = datetime.datetime.now(timezone('America/New_York'))  # 현지시각 (뉴욕 기준)
    t_today_str = t_now.strftime('%Y%m%d')  # ex) 20240101
    PATH = "uapi/overseas-stock/v1/trading/inquire-ccnl"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {g_access_token}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "JTTT3001R",
        "tr_cont": "",
        "custtype": "P"
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": "%",
        "ORD_STRT_DT": t_today_str,
        "ORD_END_DT": t_today_str,
        "SLL_BUY_DVSN": "00",  # 00: 전체, 01: 매도, 02: 매수
        "CCLD_NCCS_DVSN": "00",  # 00: 전체, 01: 체결, 02: 미체결
        "OVRS_EXCG_CD": "NASD",
        "SORT_SQN": "DS",
        "ORD_DT": "",
        "ORD_GNO_BRNO": "",
        "ODNO": "",
        "CTX_AREA_NK200": "",
        "CTX_AREA_FK200": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    today_order = res.json()['output']
    today_order_dict = {}
    while True:
        """----------------------------------------------------------------------------------"""
        for pack in today_order:
            sell_or_buy: str = 'sell' if pack['sll_buy_dvsn_cd'] == '01' else 'buy'
            today_order_list = [int(pack['ft_ord_qty']), int(pack['ft_ccld_qty']), int(pack['nccs_qty']), sell_or_buy]
            # today_order_list = [(주문수량), (체결수량), (미체결수량), (매도or매수)]    <- 미체결수량은 당일 정규장 pending order가 아니면 0
            if pack['pdno'] in today_order_dict:
                idx = 0 if sell_or_buy == 'sell' else 1
                if pack['rvse_cncl_dvsn_name'] == '취소':
                    today_order_dict[pack['pdno']][idx][0] -= int(pack['ft_ord_qty'])
                    today_order_dict[pack['pdno']][idx][1] -= int(pack['ft_ccld_qty'])
                    today_order_dict[pack['pdno']][idx][2] -= int(pack['nccs_qty'])
                    if today_order_dict[pack['pdno']][idx][0] == 0:
                        today_order_dict[pack['pdno']][idx] = ''
                    if today_order_dict[pack['pdno']] == ['', '']:
                        del today_order_dict[pack['pdno']]
                    my_print(to_print_progress, f"- '{pack['pdno']}': {today_order_list}")
                    my_print(to_print_progress, today_order_dict)
                elif isinstance(today_order_dict[pack['pdno']][idx], list):
                    today_order_dict[pack['pdno']][idx][0] += int(pack['ft_ord_qty'])
                    today_order_dict[pack['pdno']][idx][1] += int(pack['ft_ccld_qty'])
                    today_order_dict[pack['pdno']][idx][2] += int(pack['nccs_qty'])
                    my_print(to_print_progress, f"+ '{pack['pdno']}': {today_order_list}")
                    my_print(to_print_progress, today_order_dict)
                else:
                    if sell_or_buy == 'sell':
                        today_order_dict[pack['pdno']][0] = today_order_list
                    elif sell_or_buy == 'buy':
                        today_order_dict[pack['pdno']][1] = today_order_list
                    my_print(to_print_progress, f"+ '{pack['pdno']}': {today_order_list}")
                    my_print(to_print_progress, today_order_dict)
            else:
                if sell_or_buy == 'sell':
                    today_order_dict[pack['pdno']] = [today_order_list, '']
                elif sell_or_buy == 'buy':
                    today_order_dict[pack['pdno']] = ['', today_order_list]
                my_print(to_print_progress, f"+ '{pack['pdno']}': {today_order_list}")
                my_print(to_print_progress, today_order_dict)
        """----------------------------------------------------------------------------------"""
        if not res.json()['ctx_area_nk200'].isspace():  # 다음 페이지 조회
            headers['tr_cont'] = 'N'
            params['CTX_AREA_NK200'] = res.json()['ctx_area_nk200']
            params['CTX_AREA_FK200'] = res.json()['ctx_area_fk200']
            res = requests.get(URL, headers=headers, params=params)
            today_order = res.json()['output']
        else:  # 다음 페이지에 표시할 '주문체결내역'이 더 이상 없으면 'ctx_area_nk200'은 공란임
            break
        """----------------------------------------------------------------------------------"""
    # today_order_dict = {'A': ['', [1, 1, 0, 'buy']], 'B': [[6, 6, 0, 'sell'], [12, 10, 2, 'buy']]}
    return today_order_dict


def get_crnt_price_of_ordered_time(portfolio_count: int):
    portfolio_output_list = []
    update_date = ''
    flattened_crnt_price_of_ordered_time_dict = {}
    for i in range(portfolio_count):
        with open(f'./output/portfolio_output_{i + 1}.json', 'r', encoding='UTF-8') as pof:
            portfolio_output_list.append(json.load(pof))
        if update_date == portfolio_output_list[i]['update_date'] or update_date == '':
            update_date = portfolio_output_list[i]['update_date']
        for ticker, lst in portfolio_output_list[i][f'portfolio_dict_{i + 1}'].items():
            flattened_crnt_price_of_ordered_time_dict[ticker] = lst[2]

    return update_date, flattened_crnt_price_of_ordered_time_dict


def get_inquire_ccnl_order_details(to_print_progress: bool, portfolio_count: int):
    """체결내역 상세조회"""
    t_now = datetime.datetime.now(timezone('America/New_York'))  # 현지시각 (뉴욕 기준)
    t_today_str = t_now.strftime('%Y%m%d')  # ex) 20240101
    PATH = "uapi/overseas-stock/v1/trading/inquire-ccnl"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {g_access_token}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "JTTT3001R",
        "tr_cont": "",
        "custtype": "P"
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": "%",
        "ORD_STRT_DT": t_today_str,
        "ORD_END_DT": t_today_str,
        "SLL_BUY_DVSN": "00",  # 00: 전체, 01: 매도, 02: 매수
        "CCLD_NCCS_DVSN": "00",  # 00: 전체, 01: 체결, 02: 미체결
        "OVRS_EXCG_CD": "NASD",
        "SORT_SQN": "DS",
        "ORD_DT": "",
        "ORD_GNO_BRNO": "",
        "ODNO": "",
        "CTX_AREA_NK200": "",
        "CTX_AREA_FK200": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    today_order = res.json()['output']
    today_order_details_list = []
    date_of_ordered_time, flattened_crnt_price_of_ordered_time_dict = get_crnt_price_of_ordered_time(portfolio_count)

    while True:
        """----------------------------------------------------------------------------------"""
        for pack in today_order:
            ticker = pack['pdno']
            ord_qty = int(pack['ft_ord_qty']) if pack['rvse_cncl_dvsn_name'] != '취소' else -1 * int(pack['ft_ord_qty'])
            ccld_qty = int(pack['ft_ccld_qty']) if pack['rvse_cncl_dvsn_name'] != '취소' else 0
            non_ccld_qty = int(pack['nccs_qty'])
            sell_or_buy: str = 'sell' if pack['sll_buy_dvsn_cd'] == '01' else 'buy'
            ord_price = float(pack['ft_ord_unpr3'])
            ccld_price = float(pack['ft_ccld_unpr3'])
            if sell_or_buy == 'sell':  # if crnt_price != 0은, '취소'case의 division zero 에러방지
                crnt_price = flattened_crnt_price_of_ordered_time_dict[ticker]
                crnt_ord_disparate_rate = (ord_price - crnt_price) / crnt_price * 100 if crnt_price != 0 else 0
                crnt_ccld_disparate_rate = (ccld_price - crnt_price) / crnt_price * 100 if crnt_price != 0 else 0
            else:
                crnt_price = flattened_crnt_price_of_ordered_time_dict[ticker]
                crnt_ord_disparate_rate = (crnt_price - ord_price) / crnt_price * 100 if crnt_price != 0 else 0
                crnt_ccld_disparate_rate = (crnt_price - ccld_price) / crnt_price * 100 if crnt_price != 0 else 0
            ord_date = pack['ord_dt']
            ord_time = pack['ord_tmd']
            app_method = 'MTS' if pack['mdia_dvsn_name'] == '모바일' else pack['mdia_dvsn_name']  # 기본값 : OpenAPI
            if app_method == 'MTS':
                crnt_price = crnt_ord_disparate_rate = crnt_ccld_disparate_rate = 0

            today_order_details_each = [ticker, ord_qty, ccld_qty, non_ccld_qty, sell_or_buy, crnt_price, ccld_price,
                                        crnt_ccld_disparate_rate, ord_price, crnt_ord_disparate_rate, ord_date, ord_time, app_method]
            # [(종목), (주문수량), (체결수량), (미체결수량), (삼/팜) (당시현재가), ("체결가), (체결괴리율), ("주문가), (주문괴리율), (주문날짜), ("시각), (앱)]
            today_order_details_list.append(today_order_details_each)
        """----------------------------------------------------------------------------------"""
        if not res.json()['ctx_area_nk200'].isspace():  # 다음 페이지 조회
            headers['tr_cont'] = 'N'
            params['CTX_AREA_NK200'] = res.json()['ctx_area_nk200']
            params['CTX_AREA_FK200'] = res.json()['ctx_area_fk200']
            res = requests.get(URL, headers=headers, params=params)
            today_order = res.json()['output']
        else:  # 다음 페이지에 표시할 '주문체결내역'이 더 이상 없으면 'ctx_area_nk200'은 공란임
            break
        """----------------------------------------------------------------------------------"""
    my_print(to_print_progress, '상세내역  :')
    my_print(to_print_progress, '(tkr): [odr,  v,  p,  s/b|     crnt,     ccld,crt-ccld|       odr,  crnt-odr|     ', end='')
    my_print(to_print_progress, 'date,   time,  method ]')
    my_print(to_print_progress, '---------------------------------------------------------------------------------', end='')
    my_print(to_print_progress, '-----------------------')
    for today_order_details_each in today_order_details_list:
        lst = today_order_details_each
        print_str = "{0:<5}: [{1:>3},{2:>3},{3:>3},{4:>5}| ${5:>7.3f}, ${6:>7.3f}, {7:6.3f}%| (${8:>6.2f}), ({9:>6.3f}%)|{10:>9}," \
                    "{11:>7}, {12:>7} ]".format(lst[0], lst[1], lst[2], lst[3], lst[4], lst[5], lst[6], lst[7], lst[8], lst[9],
                                                lst[10], lst[11], lst[12])
        my_print(to_print_progress, print_str)
    my_print(to_print_progress, f'참고1) crnt는 주문시각({date_of_ordered_time})을 기준으로 portfolio_output_n.json에서 추출해온 것임')
    my_print(to_print_progress, f'참고2) 매도핸디캡: -{SELL_ORDER_DISADVANTAGE_RATE_PCT}%, 매수핸디캡: -{BUY_ORDER_DISADVANTAGE_RATE_PCT}%')
    print()
    return today_order_details_list


def sell(ticker='AAPL', market='NASD', qty=1, price=12.34):
    """매도(지정가)"""
    PATH = "uapi/overseas-stock/v1/trading/order"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": ticker,
        "OVRS_EXCG_CD": market,
        "ORD_DVSN": "00",  # 지정가
        "ORD_QTY": str(int(qty)),
        "OVRS_ORD_UNPR": f"{round(price, 2)}",
        "ORD_SVR_DVSN_CD": "0"
    }
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {g_access_token}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "TTTT1006U",
        "custtype": "P",
        "hashkey": hashkey(data)
    }
    res = requests.post(URL, data=json.dumps(data), headers=headers)
    if res.json()['rt_cd'] == '0':
        send_message(f'{ticker} {qty}주 매도주문 -> 성공!')
        time.sleep(2)  # Discord webhook은 분당 최대 30개의 메시지를 보낼 수 있음
        print(f'{str(res.json())}')
        return True
    else:
        send_message(f'{ticker} {qty}주 매도주문 -> 실패;')
        time.sleep(2)
        print(f'{str(res.json())}')
        return False


def buy(ticker='AAPL', market='NASD', qty=1, price=12.34):
    """매수(지정가)"""
    PATH = "uapi/overseas-stock/v1/trading/order"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": ticker,
        "OVRS_EXCG_CD": market,
        "ORD_DVSN": "00",  # 지정가
        "ORD_QTY": str(int(qty)),
        "OVRS_ORD_UNPR": f"{round(price, 2)}",
        "ORD_SVR_DVSN_CD": "0"
    }
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {g_access_token}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "TTTT1002U",
        "custtype": "P",
        "hashkey": hashkey(data)
    }
    res = requests.post(URL, data=json.dumps(data), headers=headers)
    if res.json()['rt_cd'] == '0':
        send_message(f'{ticker} {qty}주 매수주문 -> 성공!')
        time.sleep(2)
        print(f'{str(res.json())}')
        return True
    else:
        send_message(f'{ticker} {qty}주 매수주문 -> 실패;')
        time.sleep(2)
        print(f'{str(res.json())}')
        return False


def launch_order(**portfolio_dict):
    # 매도 여부 체크
    to_sell = False
    for ticker, lst in portfolio_dict.items():
        order_qty = lst[11]
        if order_qty < 0:
            to_sell = True
            break
    # 매도
    if to_sell:
        send_message(f'[매도]')
        for ticker, lst in portfolio_dict.items():
            market = lst[1]  # 시장분류
            order_qty = lst[11]  # 목표매매량(음수면 매도할 것)
            current_price = get_current_price(ticker, market)  # 현재가
            if order_qty < 0:
                order_qty = abs(order_qty)  # 실제 수량으로 변환(절대값)
                print(ticker, market, order_qty, round(current_price * (1 - SELL_ORDER_DISADVANTAGE_RATE_PCT / 100), 2))
                """주의! 실제 매도주문 작동함"""
                sell(ticker, market, order_qty, round(current_price * (1 - SELL_ORDER_DISADVANTAGE_RATE_PCT / 100), 2))
        time.sleep(5)  # 5초간 대기
    # 매수
    send_message(f'[매수]')
    for ticker, lst in portfolio_dict.items():
        market = lst[1]
        order_qty = lst[11]
        current_price = get_current_price(ticker, market)
        if order_qty > 0:
            print(ticker, market, order_qty, round(current_price * (1 + BUY_ORDER_DISADVANTAGE_RATE_PCT / 100), 2))
            """주의! 실제 매수주문 작동함"""
            buy(ticker, market, order_qty, round(current_price * (1 + BUY_ORDER_DISADVANTAGE_RATE_PCT / 100), 2))
