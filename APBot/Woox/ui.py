import tkinter as tk
from tkinter import messagebox
import requests
from tkinter import ttk


import random
import time
import json
import uuid
import hmac
import hashlib
import decimal


ORDER_CANCEL_CHECK_SEC = 20

import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import os

LOG_DIR = './logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

TOKEN_USDT = 0

TICK_SIZE = "0.0001"

def format_price(price, tick_size_str = TICK_SIZE):
    """
    틱 사이즈에 맞게 가격을 형식화합니다.
    tick_size_str 예: "0.01", "1", "0.0001"
    """
    tick_size_decimal = decimal.Decimal(tick_size_str)
    price_decimal = decimal.Decimal(str(price))
    
    # 틱 사이즈 단위로 가격을 반올림
    formatted_price = price_decimal.quantize(tick_size_decimal, rounding=decimal.ROUND_DOWN)
    return float(formatted_price)

class SizeBasedFileHandler(logging.Handler):
    def __init__(self, base_filename_only, max_bytes):
        super().__init__()
        self.base_filename_only = base_filename_only  # 예: '2025-07-06'
        self.max_bytes = max_bytes
        self.file_index = 1
        self.current_file = None
        self.open_new_file()

    def open_new_file(self):
        if self.current_file:
            self.current_file.close()
        filename = f"{self.base_filename_only}_{self.file_index:02d}.log"
        self.current_path = os.path.join(LOG_DIR, filename)  # 여기서만 LOG_DIR 붙임
        self.current_file = open(self.current_path, 'a', encoding='utf-8')
        self.file_index += 1

    def emit(self, record):
        msg = self.format(record) + '\n'
        if self.current_file.tell() + len(msg.encode('utf-8')) > self.max_bytes:
            self.open_new_file()
        self.current_file.write(msg)
        self.current_file.flush()

    def close(self):
        if self.current_file:
            self.current_file.close()
        super().close()
        
        
# 오늘 날짜 기준 파일명
today = datetime.now().strftime('%Y-%m-%d')
#base_filename = os.path.join(LOG_DIR, today)

# 핸들러 설정
handler = SizeBasedFileHandler(base_filename_only=today, max_bytes=10240)
# 로그 포맷 설정 (날짜, 로그레벨, 메시지)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)

# 로거 설정
logger = logging.getLogger("mylogger")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# 테스트 로그
#logger.info("테스트 로그: 시작됨")
#logger.warning("테스트 로그: 경고 발생")
#logger.error("테스트 로그: 에러 발생")





import os
import xml.etree.ElementTree as ET

from decimal import Decimal, ROUND_DOWN, getcontext


getcontext().prec = 18  # 충분한 소수 정밀도 설정

order_tree = None

BASE_URL = "https://api.woox.io"  # 또는 staging: https://api.staging.woox.io
ORDER_PATH = "/v3/trade/order"
ORDER_URL = BASE_URL + ORDER_PATH

def now_ms() -> str:
    """현재 시간(밀리초) 문자열 반환"""
    return str(int(time.time() * 1000))


def make_signature(secret: str, timestamp: str, method: str, path: str, body: str = "") -> str:
    """
    signature_payload = timestamp + method + path + body
    GET 요청이면 body는 빈 문자열
    path에는 쿼리스트링(token=... 등) 포함시켜야 함
    """
    payload = f"{timestamp}{method}{path}{body}"
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return sig

        
#설정파일
def read_settings(xml_file):
    if 0:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        xml_path = os.path.join(current_dir, xml_file)
        tree = ET.parse(xml_path)
    else:        
        tree = ET.parse(xml_file)
    root = tree.getroot()        
    global API_KEY, API_SECRET,  ORDER_CANCEL_CHECK_SEC    
    
    API_KEY = root.find('api_key').text
    API_SECRET = root.find('api_scret').text    
    ORDER_CANCEL_CHECK_SEC = int(root.find('order_cancel_check_time').text)        

def now_ms() -> str:
    """현재 시간(밀리초) 문자열 반환"""
    return str(int(time.time() * 1000))


BALANCES_PATH = "/v3/balances"
BALANCES_URL = BASE_URL + BALANCES_PATH

def get_balances(token: str = None, all_tokens: bool = False) -> dict:
    """
    /v3/balances 호출해서 보유자산 조회
    token: 특정 토큰만 조회 (예: "USDT")
    all_tokens: True면 잔고 0인 토큰까지 포함해서 반환
    
    
    {
  "success": true,
  "data": {
    "holding": [
      {
        "token": "GRND",
        "holding": 87734.537123,        // 전체 보유수량
        "frozen": 0,                   // 주문 등으로 묶여 있는 수량
        "staked": 0,                   // 스테이킹된 수량
        "unbonding": 0,                // 언본딩 중인 수량
        "vault": 0,                    // 금고(Vault)에 예치된 수량
        "interest": 0,                 // 이자로 발생한 수량
        "pendingShortQty": -27786.13,  // 미체결 숏 수량(음수면 빌린 상태)
        "pendingLongQty": 118292.88,   // 미체결 롱 수량
        "availableBalance": 59948.407123, // 실제 즉시 사용 가능한 잔고
        "averageOpenPrice": 0.04551873,   // 평균 매수가
        "markPrice": 0.04825,             // 현재 마크 프라이스
        "launchpadVault": 0,              // 런치패드에 예치된 수량
        "earn": 0,                        // Earn 상품에 예치된 수량
        "pnl24H": 189.00333155,           // 24시간 PnL
        "fee24H": 0.16608849,             // 24시간 수수료
        "bonus": 0,                       // 보너스
        "coverRatio": 0,                  // 마진 커버 비율
        "updatedTime": 1757581251.619     // 마지막 업데이트 시각(유닉스타임, ms)
      }
    ],
    "userId": 256293,
    "applicationId": "9151e599-b830-4c93-8ec7-6803eb90f1a1"
  },
  "timestamp": 1757634424426
}

    """
    timestamp = now_ms()
    method = "GET"

    # 쿼리스트링 구성
    params = {}
    if token:
        params["token"] = token
    if all_tokens:
        params["all"] = "true"

    # path + 쿼리스트링
    if params:
        # 예: /v3/balances?token=USDT&all=true
        qs = "&".join([f"{key}={params[key]}" for key in sorted(params)])
        path_with_qs = BALANCES_PATH + "?" + qs
    else:
        path_with_qs = BALANCES_PATH

    # body 없음 for GET
    body_str = ""

    signature = make_signature(API_SECRET, timestamp, method, path_with_qs, body_str)

    headers = {
        "x-api-key": API_KEY,
        "x-api-timestamp": timestamp,
        "x-api-signature": signature,
        "Content-Type": "application/json"
    }

    url = BASE_URL + path_with_qs

    resp = requests.get(url, headers=headers, timeout=10)
    try:
        raw = resp.content  # 또는 resp.text.encode() 등
        data = json.loads(raw)
        if data.get("success"):
            return data
    except Exception as e:
        resp.raise_for_status()
        raise e

    return None
    
#잔액조회
def update_balances_from_woox():
    try:
        data = get_balances(all_tokens = True)        
        print("전체 밸런스:", json.dumps(data, indent=2, ensure_ascii=False))
        
        if None != data:
            token_total, token_available = 0, 0
            usdt_total, usdt_available = 0, 0

            # available	사용자가 즉시 주문에 사용할 수 있는 잔액
            # frozen	이미 주문에 사용 중이라 잠겨 있는 잔액 (ex. 미체결 주문)
            # total	available + frozen 전체 자산
            
            for item in data["data"]["holding"]:
                 currency = item['token'].upper()
                 total = float(item['holding'])
                 available = float(item['availableBalance'])

                 if currency == 'GRND':
                     token_total, token_available = total, available
                 elif currency == 'USDT':
                     usdt_total, usdt_available = total, available

            token_total_label.config(text=f"전체 토큰   {token_total:,.2f}")
            token_available_label.config(text=f"가능 토큰   {token_available:,.2f}")
            usdt_total_label.config(text=f"전체 USDT    {usdt_total:,.2f}")        
            usdt_available_label.config(text=f"가능 USDT    {usdt_available:,.2f}")
            
            logger.info(f"전체 토큰   {token_total:,.2f}")
            logger.info(f"가능 토큰   {token_available:,.2f}")
            logger.info(f"전체 USDT    {usdt_total:,.2f}")        
            logger.info(f"가능 USDT    {usdt_available:,.2f}")
        


    except Exception as e:
        tk.messagebox.showerror("잔액 조회 오류", str(e))

#주문 조회        

ORDERS_PATH = "/v3/trade/orders"

def get_orders(
    symbol: str = None,
    side: str = None,
    status: str = None,
    start_time: int = None,
    end_time: int = None,
    page: int = 1,
    size: int = 25,
    with_realized_pnl: bool = False,
) -> dict:
    """
    주문 목록 조회 함수

    Parameters:
      symbol: ex) "SPOT_BTC_USDT"
      side: "BUY" or "SELL"
      status: ex) "FILLED", "NEW", "PARTIAL_FILLED", etc.
      start_time, end_time: epoch 밀리초 단위
      page: 페이지 번호 (1-indexed)
      size: 페이지당 개수
      with_realized_pnl: realized PnL 포함 여부
    """
    timestamp = now_ms()
    method = "GET"

    # 쿼리스트링 파라미터 구성
    params = {}
    if symbol:
        params["symbol"] = symbol
    if side:
        params["side"] = side
    if status:
        params["status"] = status
    if start_time:
        params["startTime"] = str(start_time)
    if end_time:
        params["endTime"] = str(end_time)
    params["page"] = str(page)
    params["size"] = str(size)
    if with_realized_pnl:
        params["withRealizedPnl"] = "true"

    # 정렬된 키 순으로 쿼리스트링 조합
    qs = "&".join(f"{key}={params[key]}" for key in sorted(params))
    path_with_qs = ORDERS_PATH + "?" + qs

    body_str = ""  # GET 이므로 빈 문자열

    signature = make_signature(API_SECRET, timestamp, method, path_with_qs, body_str)

    headers = {
        "x-api-key": API_KEY,
        "x-api-timestamp": timestamp,
        "x-api-signature": signature,
        "Content-Type": "application/x-www-form-urlencoded"
        # docs에서는 이 엔드포인트가 form-urlencoded 타입 헤더를 요구함 :contentReference[oaicite:1]{index=1}
    }

    url = BASE_URL + path_with_qs
    resp = requests.get(url, headers=headers, timeout=10)

    try:
        raw = resp.content  # 또는 resp.text.encode() 등
        data = json.loads(raw)
        if data.get("success"):
            return data.get("data")
    except Exception as e:
        resp.raise_for_status()
        raise e

    return None
    
def get_open_orders():
    try:
        data = get_orders(size = 500,page = 1, symbol = "SPOT_GRND_USDT")
        
        if None == data:           
            return
        
        orders = data['rows']
        
        total_count = len(orders)
        order_list = []

        formatted = f"주문 총 개수 :{total_count}\n"

        for order in orders:
            formatted += f'[종류/주문Id]:{order["side"]}/{order["orderId"]}\n'            
            type = order["type"]
            notional = 0
            price = 0
          
            if order.get('status') and (order['status'] == 'CANCELLED' or order['status'] == 'FILLED'): 
                continue
            
            if type != 'MARKET':                
                price = float(order["price"])
                notional = float(order["price"]) * float(order["quantity"])
            formatted += f'[가격/개수/총액]:{price}/{float(order["quantity"])}/{notional}\n'
            #formatted += f'[평 단 가]:{float(order["priceAvg"])}\n'            
            timestamp_sec = float(order["createdTime"]) #) / 1000  # 밀리초 → 초
            dt = datetime.fromtimestamp(timestamp_sec)
            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            
            formatted += f'[타입/거래 시간]:{order["type"]}/{formatted_time}\n'            
            
                
            order_list.append({                
                "orderId": order["orderId"],
                "side": order["side"],         # buy/sell
                "price": float(price),
                "size": float(order["quantity"]),
                "notional": float(notional),  # 주문 총액 (price * size)
                "type": type,         # 보통은 'limit'
                "state": order["status"],       # submitted 등
                "createTime": order["createdTime"]
            })

        return [order_list,formatted]

    except Exception as e:
        print("주문 조회 실패:", str(e))
        return [],f"주문 조회 실패:{str(e)}"
        
ALL_ORDERS_BY_SYMBOL_PATH = "/v3/trade/allOrders"

def cancel_all_orders_by_symbol(symbol: str, side: str = None, positionSide: str = None) -> dict:
    """
    특정 심볼의 모든 주문 취소 (ordinary + algo) 문서에 따르면 가능함
    side / positionSide 옵션은 선택사항
    """
    timestamp = now_ms()
    method = "DELETE"
    path = ALL_ORDERS_BY_SYMBOL_PATH

    # form data params
    params = {"symbol": symbol}
    if side:
        params["side"] = side
    if positionSide:
        params["positionSide"] = positionSide

    body_str = "&".join(f"{k}={params[k]}" for k in sorted(params))
    path_with_qs = path

    signature = make_signature(API_SECRET, timestamp, method, path_with_qs, body_str)

    headers = {
        "x-api-key": API_KEY,
        "x-api-timestamp": timestamp,
        "x-api-signature": signature,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    url = BASE_URL + path
    resp = requests.delete(url, headers=headers, data=params, timeout=10)
    try:
        return  resp.json()
    except Exception:
        return ""
    

def cancel_order_v3(order_id=None,  symbol=None):
    timestamp = now_ms()
    method = "DELETE"
    path = "/v3/trade/order"

    params = {}
    if order_id:
        params["orderId"] = str(order_id)
    
    if symbol:
        params["symbol"] = symbol

    # 정렬된 키 순서로 form 문자열 생성 (signature consistency)
    body_str = "&".join(f"{k}={params[k]}" for k in sorted(params))

    signature= make_signature(API_SECRET, timestamp, method, path, body_str)

    headers = {
        "x-api-key": API_KEY,
        "x-api-timestamp": timestamp,
        "x-api-signature": signature,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    url = BASE_URL + path
    
    
    
    try:
        resp = requests.delete(url, headers=headers, data=body_str.encode('utf-8'), timeout=10)
        return resp.json()
    except Exception as e:
        return f"error:{e}"
        

    return None
    
#주문 취소        
def cancel_filtered_orders(gap_min, gap_max, cancel_order=False, side_filter=None):
    """
    TOKEN_USDT 주문 중 가격이 시장가 ± cancel_rate% 이내인 지정 side 주문을 오래된 순으로 취소
    :param token_usdt_price: 현재 시장가
    :param cancel_rate: 허용 비율 (%)
    :param side_filter: 'buy' 또는 'sell' 또는 None (전체)
    """
    global TOKEN_USDT
    
    
    price = 0
    precision = 5  # 비교 정밀도

    min_sell_price = TOKEN_USDT * (1 + gap_min / 100)
    max_sell_price = TOKEN_USDT * (1 + gap_max / 100)
    
    min_buy_price = TOKEN_USDT * (1 - gap_max / 100)
    max_buy_price = TOKEN_USDT * (1 - gap_min / 100)
    
    min_sell_price = round(min_sell_price, precision)
    max_sell_price = round(max_sell_price, precision)
    
    min_buy_price = round(min_buy_price, precision)
    max_buy_price = round(max_buy_price, precision)
        
    msg = f"[INFO] 주문 취소 체크 API:{cancel_order}\n"
    msg += f"[INFO] cur:{TOKEN_USDT}\n"        
    msg += f"[INFO] min_sell_price:{min_sell_price:.8f}, min_sell_price:{max_sell_price:.8f}\n"   
    msg += f"[INFO] min_buy_price:{min_buy_price:.8f}, max_buy_price:{max_buy_price:.8f}\n"   
    
    logger.info(f"주문 취소 체크 API:{cancel_order}")
    logger.info(f"cur:{TOKEN_USDT}")
    logger.info(f"min_sell_price:{min_sell_price:.8f}, min_sell_price:{max_sell_price:.8f}")
    logger.info(f"min_buy_price:{min_buy_price:.8f}, max_buy_price:{max_buy_price:.8f}")
    
    
    try:        
        data = get_orders(size = 500,page = 1, symbol = "SPOT_GRND_USDT")
        
        if None == data:           
            return
        
        filtered = []
        
        orders = data['rows']
        
        total_count = len(orders)
      

        #formatted = f"주문 총 개수 :{total_count}\n"

        
        for order in orders:
            #취소된것들은 의미업삳
            if order.get('status') and (order['status'] == 'CANCELLED' or order['status'] == 'FILLED'):
                continue
            
            price = 0
            if order.get('price'):
                price = float(order['price'])
                price = round(float(order['price']), precision)
            side = order['side']
            
            
            
            
            type = order["type"]
            
            if type == 'MARKET': 
                continue
                
            if "BUY" == side:
                min_price,max_price = min_buy_price,max_buy_price
            else:
                min_price,max_price = min_sell_price,max_sell_price
                
                
           
            
            if price < min_price or price > max_price:
                if side_filter is None or side == side_filter.lower():
                    filtered.append({
                        "orderId": order["orderId"],
                        "side": side,
                        "price": price,
                        "timestamp": float(order["createdTime"])
                    })

        # 오래된 주문 우선 정렬
        filtered.sort(key=lambda x: x["timestamp"])        
        msg += f"[INFO] 총 {len(filtered)}건 조건 충족 주문 발견됨. 취소 진행...\n"
        
        logger.info(f"[INFO] 총 {len(filtered)}건 조건 충족 주문 발견됨. 취소 진행...")
        print(f"[INFO]총 {len(filtered)}건 조건 충족 주문 발견됨. 취소 진행...")

        cancel_count = 0
        failed_cancel_count = 0
        for order in filtered:
            orderId = order["orderId"]
            sucess = False
            submit_msg=""
            try:
                
                if cancel_order:
                    cancel_res = cancel_order_v3(symbol='SPOT_GRND_USDT', order_id=orderId)
                    if cancel_res['success'] == True:
                        cancel_res = True                        
                        submit_msg = post_submit_ordersfor_cancel(order['side'],True)                        
                        sucess = True
                else:
                    sucess = True
                    submit_msg = post_submit_ordersfor_cancel(order['side'],False)
                    
                    
                if sucess:
                    msg += f"[OK] 취소됨: {order['side']} @ {order['price']} / ID: {orderId}\n"
                    msg += submit_msg
                    
                    logger.info(f"[OK] 취소됨: {order['side']} @ {order['price']} / ID: {orderId}")
                    logger.info(submit_msg)                    
                    print(f"[OK] 취소됨: {order['side']} @ {order['price']} / ID: {orderId}")
                    print(submit_msg)
                    cancel_count += 1
                else:
                    msg += f"[Failed] 취소실패: {order['side']} @ {order['price']} / ID: {orderId}\n"
                    msg+=submit_msg
                    
                    logger.info(f"[Failed] 취소실패: {order['side']} @ {order['price']} / ID: {orderId}")
                    logger.info(submit_msg)
                    
                    print(f"[Failed] 취소실패: {order['side']} @ {order['price']} / ID: {orderId}")
                    print(submit_msg)
                    failed_cancel_count += 1
            except Exception as cancel_err:
                msg += f"\n[FAIL] 취소 실패 (ID: {orderId}): {cancel_err}"
                print(f"[FAIL] 취소 실패 (ID: {orderId}): {cancel_err}")
                logger.error(f"[FAIL] 취소 실패 (ID: {orderId}): {cancel_err}")

        msg += f"\n[DONE] 총 {cancel_count}건 성공 {failed_cancel_count}건 실패."        
        logger.info(f"[DONE] 총 {cancel_count}건 성공 {failed_cancel_count}건 실패.")
        print(f"\n[DONE] 총 {cancel_count}건 성공 {failed_cancel_count}건 실패.")

    except Exception as e:
        msg += f"\n[ERROR] 주문 필터링 실패: {e}"
        print(f"[ERROR] 주문 필터링 실패: {e}")
        logger.error(f"[ERROR] 주문 필터링 실패: {e}")
    
    update_order_table(True)
    return msg

from urllib.parse import urlencode

def _generate_signature(data):
  key = API_SECRET#'key' # Defined as a simple string.
  key_bytes= bytes(key , 'utf-8') # Commonly 'latin-1' or 'utf-8'
  data_bytes = bytes(data, 'utf-8') # Assumes `data` is also a string.
  return hmac.new(key_bytes, data_bytes , hashlib.sha256).hexdigest()

def place_order(symbol: str, side: str,  quantity: str = None, price: str = None, ):
    milliseconds_since_epoch = round(datetime.now().timestamp() * 1000)
    
    headers = {
        'x-api-timestamp': str(milliseconds_since_epoch),
        'x-api-key': str(API_KEY),
        'x-api-signature': _generate_signature(f"order_price={price}&order_quantity={quantity}&order_type=LIMIT&side={side}&symbol={symbol}|"+str(milliseconds_since_epoch)),
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cache-Control':'no-cache'
    }
    data = {
    #'client_order_id':{clientid},
    'order_price' : {price},
    'order_quantity': {quantity},
    'order_type': 'LIMIT',
    'side':{side},
    'symbol': {symbol}
    }
    
    response = requests.post('https://api.woox.io/v1/order', headers=headers, data=data )
    return response.json()

    

def submit_orders(side, canAPI):
    global TOKEN_USDT
    
    gap_min = float(gap_min_entry.get())
    gap_max = float(gap_max_entry.get())
    
    amount_min = float(amount_min_entry.get())
    amount_max = float(amount_max_entry.get())
    
    
    gap = random.uniform(gap_min, gap_max)
    price = 0
    if side =="SELL":
        price = TOKEN_USDT * (1 + gap / 100)
    else:
        price = TOKEN_USDT * (1 - gap / 100)    
    
    #price = TOKEN_USDT * (1 + gap / 100)  # 예: 갭 0.5% 상승
    # raw_price = TOKEN_USDT * (1 + gap / 100)  # 예: 갭 0.5% 상승
    
    # price_unit = Decimal('0.00001')
    # raw_price = Decimal(str(raw_price))  # float → str → Decimal

    # # 최소단위에 맞게 반올림 또는 내림
    # price = (raw_price / price_unit).to_integral_value(rounding=ROUND_DOWN) * price_unit
    
    # price = float(price)

    total_amount = random.uniform(amount_min, amount_max)
    size = round(total_amount / price, 2)  # ADP 수량 (소수점 2자리로 제한)        
    price = format_price(price) #소수점 자리수 변경
    
    msg = f'[주문] {side} price:{price:.8f}, size:{size:.5f}\n'
    logger.info(f'[주문] {side} price:{price:.8f}, size:{size:.5f}')
    
    
    
    try:
        if canAPI:
            res = place_order(                
                'SPOT_GRND_USDT',     # 거래쌍                
                side,            # 'buy' 또는 'sell'
                #order_type='limit',    # 주문 유형 ('limit' 또는 'market')
                size,         # 수량 (GRND 개수)
                price        # 가격 (USDT 기준)
            )
            msg += f"[주문]주문 결과:{res}\n"
            logger.info(f'[주문]주문 결과:{res}')
    except Exception as err:
        msg += f"{err}\n"
        msg += f"[FAIL] {side} 주문 실패 (gap:{gap:.8f}), price:{price:.2f}, size:{size:.2f}\n"
        logger.error(f"{err}")
        logger.error(f"[FAIL] {side} 주문 실패 (gap:{gap:.8f}), price:{price:.2f}, size:{size:.2f}")
        print(msg)
        
    
    return msg

#side ="BUY" , "SELL"
def post_submit_orders(canAPI = False):    
    if gap_min_entry.get().strip() == "" or  gap_max_entry.get().strip() == "" or amount_min_entry.get().strip() == "" or amount_max_entry.get().strip() == ""  or count_entry.get().strip() == "":
        messagebox.showwarning("입력 누락", "최소 갭 값을 입력하세요.")
        return
    
    if float(amount_min_entry.get()) <= 5.0 or float(amount_max_entry.get()) <= 5.0:
        messagebox.showwarning("입력오류", "최소 USTD 값 5 초과해야된다.")
        return
        

    order_count = int(count_entry.get())
    
    global TOKEN_USDT
    msg = f"[주문]가져온 가격: usdt{TOKEN_USDT:.5f}\n"
    logger.info(f"[주문]가져온 가격: usdt{TOKEN_USDT:.5f}")
    
    for _ in range(order_count):
        message = submit_orders('BUY',canAPI)
        msg += message
        
    for _ in range(order_count):
        message = submit_orders('SELL',canAPI)
        msg += message
    
    print(msg)              
    
    update_order_table(True)
    
    return msg
    

#취소된 주문 다시 하기
def post_submit_ordersfor_cancel(side, canAPI = False):    
    if gap_min_entry.get().strip() == "" or  gap_max_entry.get().strip() == "":
        messagebox.showwarning("입력 누락", "최소 갭 값을 입력하세요.")
        return
    
    if float(amount_min_entry.get()) <= 5.0 or float(amount_max_entry.get()) <= 5.0:
        messagebox.showwarning("입력오류", "최소 USTD 값 5 초과해야된다.")
        return    
    
    msg = submit_orders(side,canAPI)
    
    print(msg)
    return msg        
        
# 초기 상태
status = "중지"


sort_directions = {}  # 정렬 상태 저장용

def create_order_table_window(root):
    global order_tree, sort_directions

    win = tk.Toplevel(root)
    win.title("Orders -30초마다 갱신")
    win.geometry("900x400")

    columns = ("orderId", "side", "price", "size", "notional", "type", "createTime")

    order_tree = ttk.Treeview(win, columns=columns, show='headings')
    order_tree.pack(expand=True, fill='both')

    for col in columns:
        sort_directions[col] = False  # 초기 정렬 방향: 오름차순
        order_tree.heading(col, text=col, command=lambda _col=col: sort_column(_col))

        order_tree.column(col, width=120)

    #tk.Button(win, text="닫기", command=win.destroy).pack(pady=5)

    # 최초 데이터 채움
    update_order_table()
    
def sort_column(col):
    global order_tree, sort_directions

    # 정렬 방향 가져오기 (False: 오름차순, True: 내림차순)
    reverse = sort_directions[col]

    # 현재 데이터 가져오기
    data = [(order_tree.set(k, col), k) for k in order_tree.get_children('')]

    # 정렬 (숫자/문자 구분)
    try:
        data.sort(key=lambda t: float(t[0]), reverse=reverse)
    except ValueError:
        data.sort(key=lambda t: t[0], reverse=reverse)

    # 정렬된 순서대로 재배치
    for index, (val, k) in enumerate(data):
        order_tree.move(k, '', index)

    # 정렬 방향 토글 저장
    sort_directions[col] = not reverse

    # 헤더 텍스트 리셋 (▲▼ 표시 추가)
    for c in order_tree["columns"]:
        arrow = ""
        if c == col:
            arrow = " ▲" if not reverse else " ▼"
        order_tree.heading(c, text=c + arrow, command=lambda _col=c: sort_column(_col))
    
def update_order_table(refresh = False):
    global order_tree

    if not order_tree:
        return

    orders, _ = get_open_orders()

    # 기존 데이터 삭제
    for row in order_tree.get_children():
        order_tree.delete(row)

    # 새 데이터 삽입
    if orders :
        for order in orders:
            ts = float(order['createTime'])
            formatted_time = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            order_tree.insert('', 'end', values=(
                order['orderId'],
                order['side'],
                f"{order['price']:.8f}",
                f"{order['size']:.2f}",
                f"{order['notional']:.2f}",
                order['type'],
                formatted_time
            ))
    
    row_count = len(orders)    
    order_tree.master.title(f"Orders - 총 {row_count}개 (30초마다 갱신)")

    # 30초마다 갱신
    if False == refresh:
        order_tree.after(30000, update_order_table)  # 30,000ms = 30초
    
def show_order_table_window(title, orders):
    win = tk.Toplevel()
    win.title(title)
    win.geometry("900x400")

    columns = ("orderId", "side", "price", "size", "notional", "type", "createTime")

    tree = ttk.Treeview(win, columns=columns, show='headings')
    tree.pack(expand=True, fill='both')

    # 각 컬럼 제목 설정
    tree.heading("orderId", text="주문 ID")
    tree.heading("side", text="종류")
    tree.heading("price", text="가격")
    tree.heading("size", text="개수")
    tree.heading("notional", text="총액")
    tree.heading("type", text="타입")
    tree.heading("createTime", text="거래시간")

    # 컬럼 너비 지정 (원하는대로 조정)
    tree.column("orderId", width=150)
    tree.column("side", width=60)
    tree.column("price", width=80)
    tree.column("size", width=80)
    tree.column("notional", width=100)
    tree.column("type", width=80)
    tree.column("createTime", width=160)

    # 데이터 삽입
    for order in orders:
        ts = int(order['createTime']) // 1000
        formatted_time = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        tree.insert('', 'end', values=(
            order['orderId'],
            order['side'],
            f"{order['price']:.8f}",
            f"{order['size']:.2f}",
            f"{order['notional']:.2f}",
            order['type'],
            formatted_time
        ))

    # 닫기 버튼
    tk.Button(win, text="닫기", command=win.destroy).pack(pady=5)
    

def show_result_window(title, message):
    result_win = tk.Toplevel()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result_win.title(f"{now} | {title}")
    result_win.geometry("800x400")

    # 스크롤 가능한 텍스트 박스
    text_box = tk.Text(result_win, wrap='word')
    text_box.pack(expand=True, fill='both', padx=10, pady=10)

    # 내용 출력
    text_box.insert('end', message)
    text_box.config(state='disabled')  # 읽기 전용
    
    close_btn = tk.Button(result_win, text="닫기", command=result_win.destroy)
    close_btn.pack(pady=5)


def update_status(new_status):
    global status
    status = new_status
    status_label.config(text=f"자동호가봇 상대 : {status}")

def start_bot():
    
    global cancel_order_toggle_loop_running
    
    if cancel_order_toggle_loop_running:
        messagebox.showwarning("오류", "거래 취소체크 스케쥴이 돌고있습니다")
        return
    
    if gap_min_entry.get().strip() == "" or  gap_max_entry.get().strip() == "":
        messagebox.showwarning("입력 누락", "최소 갭 값을 입력하세요.")
        return
    
    if float(amount_min_entry.get()) <= 5.0 or float(amount_max_entry.get()) <= 5.0:
        messagebox.showwarning("입력오류", "최소 USTD 값 5 초과해야된다.")
        return
    
    fetch_adp_price()
    update_balances_from_woox()
    post_submit_orders(True)
    
    
    cancel_order_toggle_loop_running = True
    start_cancel_order_loop()    
    print("거래취소체크 루프 시작됨")
    logger.info("거래취소체크 루프 시작됨")    
    
    update_status("동작중")
    

def stop_bot():
    #루프중지
    global cancel_order_toggle_loop_running
    
    stop_cancel_order_loop()
    cancel_order_toggle_loop_running =False            
    print("거래취소체크 루프 중지됨")
    logger.info("거래취소체크 루프 중지됨")
        
    update_status("중지")

def cancel_all_orders():
    confirm = messagebox.askyesno("확인", "정말로 모든 TOKEN_USDT 주문을 취소하시겠습니까?")
    if not confirm:
        return  # 사용자가 "아니오" 선택 시 취소
    
    msg = ""
    #매수 취소
    try:    
        
        res = cancel_all_orders_by_symbol(
            symbol='SPOT_GRND_USDT',     # 거래쌍
            #side='buy'            # 'buy' 또는 'sell'            
        )
        msg += f"[모든 주문 취소] 결과:{res}\n"
        logger.info(f'[모든  주문 취소] 결과:{res}')
    except Exception as err:        
        msg += f"[FAIL] [모든  주문 취소] : {err}\n"        
        logger.error(f"[FAIL] [모든  주문 취소]: {err}")
        print(msg)
    
        
    messagebox.showinfo("알림", "모든 주문을 취소했습니다.")
    
def cancel_order_cancel_rate():
    
    if gap_min_entry.get().strip() == "" or  gap_max_entry.get().strip() == "":
        messagebox.showwarning("입력 누락", "최소 갭 값을 입력하세요.")
        return
    
    if float(amount_min_entry.get()) <= 5.0 or float(amount_max_entry.get()) <= 5.0:
        messagebox.showwarning("입력오류", "최소 USTD 값 5 초과해야된다.")
        return
    
    gap_min = float(gap_min_entry.get())
    gap_max = float(gap_max_entry.get())    
    
    message = cancel_filtered_orders(gap_min, gap_max, False)
    show_result_window("Order Cancel 결과", message)
    
def cancel_order_cancel_rate2():
    if gap_min_entry.get().strip() == "" or  gap_max_entry.get().strip() == "":
        messagebox.showwarning("입력 누락", "최소 갭 값을 입력하세요.")
        return
    
    if float(amount_min_entry.get()) <= 5.0 or float(amount_max_entry.get()) <= 5.0:
        messagebox.showwarning("입력오류", "최소 USTD 값 5 초과해야된다.")
        return
    
    gap_min = float(gap_min_entry.get())
    gap_max = float(gap_max_entry.get())                
    message = cancel_filtered_orders(gap_min, gap_max, True)
    show_result_window("Order Cancel 결과", message)


def cancel_order_checking(canApi):
    global status
    if gap_min_entry.get().strip() == "" or  gap_max_entry.get().strip() == "":
        messagebox.showwarning("입력 누락", "최소 갭 값을 입력하세요.")
        return
    
    if float(amount_min_entry.get()) <= 5.0 or float(amount_max_entry.get()) <= 5.0:
        messagebox.showwarning("입력오류", "최소 USTD 값 5 초과해야된다.")
        return
    
    fetch_adp_price()    
    update_balances_from_woox()
    gap_min = float(gap_min_entry.get())
    gap_max = float(gap_max_entry.get())                
    
    message = cancel_filtered_orders(gap_min, gap_max, canApi)   
    if status != "동작중":
        show_result_window("Order Cancel 결과", message)


def stop_cancel_order_loop():
    global cancel_order_toggle_loop_running, cancel_order_toggle_loop_job_id
    if cancel_order_toggle_loop_job_id is not None:
        root.after_cancel(cancel_order_toggle_loop_job_id)
        cancel_order_toggle_loop_job_id = None
        
cancelOrderFirstTime = True 
def start_cancel_order_loop():
    global cancel_order_toggle_loop_running, cancel_order_toggle_loop_job_id,cancelOrderFirstTime
    if False == cancelOrderFirstTime:
        cancel_order_checking(True)
        
    cancelOrderFirstTime = False    
        
    cancel_order_toggle_loop_job_id = root.after(ORDER_CANCEL_CHECK_SEC* 1000, start_cancel_order_loop) # 20000ms = 20초
    
def cancel_order_toggle_loop():
    if gap_min_entry.get().strip() == "" or  gap_max_entry.get().strip() == "":
        messagebox.showwarning("입력 누락", "최소 갭 값을 입력하세요.")
        return
    
    if float(amount_min_entry.get()) <= 5.0 or float(amount_max_entry.get()) <= 5.0:
        messagebox.showwarning("입력오류", "최소 USTD 값 5 초과해야된다.")
        return
    global ORDER_CANCEL_CHECK_SEC
    global cancel_order_toggle_loop_running
    if cancel_order_toggle_loop_running:
        #루프중지
        stop_cancel_order_loop()
        cancel_order_toggle_loop_running =False        
        btn_title = f"{ORDER_CANCEL_CHECK_SEC}초마다 거래취소체크: 비활성"
        test5_btn.config(text=btn_title)            
        print("거래취소체크 루프 중지됨")
        logger.info("거래취소체크 루프 중지됨")
    else:
        cancel_order_toggle_loop_running = True
        start_cancel_order_loop()
        btn_title = f"{ORDER_CANCEL_CHECK_SEC}초마다 거래취소체크: 활성"
        test5_btn.config(text=btn_title)                    
        print("거래취소체크 루프 시작됨")
        logger.info("거래취소체크 루프 시작됨")
    
    
def submit_adp_orders():    
    message = post_submit_orders()
    if 0 == len(message):
        return
    
    show_result_window("사기테스트", message)
    
    #orders , message = get_open_adp_orders()
    #show_result_window("Open Orders 조회", message)
    #show_order_table_window("Open Orders 표 형태", orders)
    
def submit_adp_orders2():
    message = post_submit_orders(True)
    if 0 == len(message):
        return
    show_result_window("사기테스트", message)

    
def get_usdt_krw_rate():
    try:
        # url = "https://api.coinbase.com/v2/exchange-rates?currency=USDT"
        # response = requests.get(url,timeout=5)
        # data = response.json()
        # return float(data["data"]["rates"]["KRW"])
                
       url = "https://api.bithumb.com/public/ticker/USDT"
       response = requests.get(url,timeout=5)
       data = response.json()
       return float(data['data']['closing_price'])
            
    except Exception as e:
        print("환율 조회 실패:", e)
        return 1300.0  # fallback

def fetch_adp_price():
    try:
        # ADP 가격 (KRW)
        url = "https://api.bithumb.com/public/ticker/GRND_KRW"
        response = requests.get(url)
        data = response.json()

        adp_krw = float(data['data']['closing_price'])
        
        # USDT 환율 (KRW)
        usdt_rate = get_usdt_krw_rate()        
        
        token_usdt = adp_krw / usdt_rate
        
        global TOKEN_USDT ,ADP_KRW        
        TOKEN_USDT, ADP_KRW =  token_usdt ,adp_krw

        price_label.config(text=f"현재 빗썸 GRND 가격 : {adp_krw:.4f}원, {token_usdt:.7f}USDT")
        #messagebox.showinfo("ADP 가격", f"ADP 가격을 불러왔습니다:\n{adp_krw:.4f} KRW / {token_usdt:.7f} USDT")
    except Exception as e:
        messagebox.showerror("오류", f"가격 조회 실패: {str(e)}")

root = tk.Tk()
root.title("자동호가봇")
root.geometry("500x600")

# 동작 상태 표시
status_label = tk.Label(root, text="자동호가봇 상대 : 중지", anchor="w")
status_label.pack(fill="x")

frame = tk.Frame(root, bd=2, relief="solid", padx=10, pady=10)
frame.pack(padx=10, pady=10, fill="both", expand=True)

# 버튼들
btn_frame = tk.Frame(frame)
btn_frame.pack(anchor="w")

start_btn = tk.Button(btn_frame, text="시작", width=8, command=start_bot)
stop_btn = tk.Button(btn_frame, text="중지", width=8, command=stop_bot)
cancel_btn = tk.Button(btn_frame, text="모든 주문 취소", width=20, command=cancel_all_orders)

test1_btn = tk.Button(btn_frame, text="order_cancel(설정된%, api호출x)", width=40, command=cancel_order_cancel_rate)
test2_btn = tk.Button(btn_frame, text="order_cancel(설정된%, api호출)", width=40, command=cancel_order_cancel_rate2)
test3_btn = tk.Button(btn_frame, text="주문하기(테스트,api호출x)", width=40, command=submit_adp_orders)
test4_btn = tk.Button(btn_frame, text="주문하기(테스트,api호출)", width=40, command=submit_adp_orders2)

cancel_order_toggle_loop_running = False
cancel_order_toggle_loop_job_id = 0
btn_title = f"{ORDER_CANCEL_CHECK_SEC}초마다 거래취소체크: 비활성"
test5_btn = tk.Button(btn_frame, text=btn_title, width=40, command=cancel_order_toggle_loop)



start_btn.grid(row=0, column=0, padx=2, pady=2)
stop_btn.grid(row=0, column=1, padx=2, pady=2)
cancel_btn.grid(row=1, column=0, columnspan=2, pady=2)
test1_btn.grid(row=2, column=0, padx=2, pady=2)
test2_btn.grid(row=3, column=0, padx=2, pady=2)
test3_btn.grid(row=4, column=0, padx=2, pady=2)
test4_btn.grid(row=5, column=0, padx=2, pady=2)
test5_btn.grid(row=6, column=0, padx=2, pady=2)

# 정보 출력
# info_texts = [
#     "전체 토큰     100,000",
#     "가능 토큰      90,000",
#     "전체 USDT     100,000",
#     "가능 USDT      90,000"
# ]

# for text in info_texts:
#     tk.Label(frame, text=text, anchor="w").pack(fill="x")

token_total_label = tk.Label(frame, text="전체 토큰     0", anchor="w")
token_total_label.pack(fill="x")

token_available_label = tk.Label(frame, text="가능 토큰      0", anchor="w")
token_available_label.pack(fill="x")

usdt_total_label = tk.Label(frame, text="전체 USDT     0", anchor="w")
usdt_total_label.pack(fill="x")

usdt_available_label = tk.Label(frame, text="가능 USDT      0", anchor="w")
usdt_available_label.pack(fill="x")

# 갭 세팅 (범위 입력)
gap_frame = tk.Frame(frame)
gap_frame.pack(anchor="w", pady=(10, 0))
tk.Label(gap_frame, text="갭 세팅").pack(side="left")

gap_min_entry = tk.Entry(gap_frame, width=5)
gap_min_entry.pack(side="left")

tk.Label(gap_frame, text="부터").pack(side="left")

gap_max_entry = tk.Entry(gap_frame, width=5)  # gap_entry2 → 이름 변경
gap_max_entry.pack(side="left")

tk.Label(gap_frame, text="%").pack(side="left")

# 금액 세팅 (범위 입력)
amount_frame = tk.Frame(frame)
amount_frame.pack(anchor="w")

tk.Label(amount_frame, text="금액 세팅").pack(side="left")

amount_min_entry = tk.Entry(amount_frame, width=10)
amount_min_entry.pack(side="left")

tk.Label(amount_frame, text="부터").pack(side="left")

amount_max_entry = tk.Entry(amount_frame, width=10)
amount_max_entry.pack(side="left")

tk.Label(amount_frame, text="단위: USDT").pack(side="left")

# 주문 갯수
count_frame = tk.Frame(frame)
count_frame.pack(anchor="w", pady=(5, 0))
tk.Label(count_frame, text="주문 갯수").pack(side="left")
count_entry = tk.Entry(count_frame, width=5)
count_entry.pack(side="left")
tk.Label(count_frame, text="개").pack(side="left")

# 가격 표시
price_label = tk.Label(frame, text="현재 빗썸 GRND 가격 : 100원, 0.1USDT", anchor="w")
price_label.pack(fill="x", pady=(10, 0))

# ADP 가격 가져오기 버튼
fetch_btn = tk.Button(root, text="GRND 가격 가져오기", command=fetch_adp_price)
fetch_btn.pack(pady=5)

# 설명
bottom_text = tk.Label(
    root,
    text=(
        "토큰수량, USDT 수량확인, 모든주문취소버튼, START, STOP 버튼이 필요합니다.\n"
        "동작시에는 동작중, 중지시에는 중지라고 표기합니다.\n\n"        
    ),
    justify="left"
)
bottom_text.pack(padx=10, anchor="w")

logger.info(f"프로그램 구동")

read_settings("setting.xml")
fetch_adp_price()
update_balances_from_woox()

# 표 형태 윈도우를 프로그램 시작과 동시에 띄움
create_order_table_window(root)




root.mainloop()



