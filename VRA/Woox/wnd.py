import tkinter as tk
from tkinter import ttk
import random
import threading
from datetime import datetime, timedelta
import time
import random

from bitmart.api_spot import APISpot
from bitmart.lib import cloud_exceptions
from datetime import datetime

import os
import xml.etree.ElementTree as ET

from decimal import Decimal

import requests
import hmac
import hashlib
import json
import decimal

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

class BithumbBotGUI:
    BASE_URL = "https://api.woox.io"
    #설정파일
    def read_settings(self,xml_file):
        if 0:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            xml_path = os.path.join(current_dir, xml_file)
            tree = ET.parse(xml_path)
        else:        
            tree = ET.parse(xml_file)
        root = tree.getroot()                
        
        self.API_KEY = root.find('api_key').text
        self.API_SECRET = root.find('api_scret').text        
          
    
    def __init__(self, root):       
        
        self.root = root
        self.root.title("VRA(Woox) - 중지")
        self.root.geometry("420x250")
        self.symbol = "SPOT_GRND_USDT"

        self.running = False
        self.schedule_thread = None
        
        self.read_settings("setting.xml")
        
        self.status_label = tk.Label(root, text="GRND_USDT 가격 정보 로딩 중...", fg="gray", font=("맑은 고딕", 10, "bold"))
        self.status_label.pack(pady=3)
        
        self.error_label = tk.Label(root, text="[오류중지]:None ", fg="blue", font=("맑은 고딕", 8))
        self.error_label.pack(pady=3)


        # 버튼 프레임
        self.btn1 = tk.Button(root, text="buy->sell 70% sell->buy 30%", command=lambda: self.start_bot(mode=70), state=tk.NORMAL, fg="red")
        self.btn1.pack(pady=5)

        self.btn2 = tk.Button(root, text="buy->sell 30% sell->buy 70%", command=lambda: self.start_bot(mode=30), state=tk.NORMAL, fg="red")
        self.btn2.pack(pady=5)

        self.stop_btn = tk.Button(root, text="Stop", command=self.stop_bot, state=tk.DISABLED)
        self.stop_btn.pack(pady=5)

        # 금액 입력 (새로운 행)
        amount_frame = tk.Frame(root)
        amount_frame.pack(pady=5)

        self.amount_min_entry = tk.Entry(amount_frame, width=10)
        self.amount_min_entry.insert(0, "1")
        self.amount_min_entry.pack(side=tk.LEFT, padx=5)

        self.amount_max_entry = tk.Entry(amount_frame, width=10)
        self.amount_max_entry.insert(0, "2")
        self.amount_max_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(amount_frame, text="금액").pack(side=tk.LEFT, padx=5)

        # 시간 입력 (새로운 행)
        time_frame = tk.Frame(root)
        time_frame.pack(pady=5)

        self.time_min_entry = tk.Entry(time_frame, width=5)
        self.time_min_entry.insert(0, "5")
        self.time_min_entry.pack(side=tk.LEFT, padx=5)

        self.time_max_entry = tk.Entry(time_frame, width=5)
        self.time_max_entry.insert(0, "20")
        self.time_max_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(time_frame, text="초").pack(side=tk.LEFT)
        
        self.get_mid_price()

    def start_bot(self, mode):
        if self.running:
            return

        self.running = True
        self.set_buttons_state(active=False)

        self.schedule_thread = threading.Thread(target=self.run_schedule, args=(mode,))
        self.schedule_thread.daemon = True
        self.schedule_thread.start()
        self.root.title("VRA - 동작 중...")
        
        

    def stop_bot(self):
        self.running = False
        self.set_buttons_state(active=True)
        self.root.title("VRA - 중지")

    def set_buttons_state(self, active=True):
        if active:
            self.btn1.config(state=tk.NORMAL)
            self.btn2.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
        else:
            self.btn1.config(state=tk.DISABLED)
            self.btn2.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
    def _get_auth_headers(self, method: str, path: str, body: dict = None, params: dict = None):
        """
        Woox 인증 헤더 만드는 함수
        문서에서 요구하는 방식 따라 수정 필요
        예: x-api-key, x-api-timestamp, x-api-signature 등
        """
        ts = str(int(time.time() * 1000))
        body_str = json.dumps(body, separators=(",", ":")) if body else ""
        # path + ts + body 또는 params 조합하여 signature 생성 (문서대로)
        to_sign = ts + method.upper() + path + body_str
        signature = hmac.new(self.API_SECRET.encode(), to_sign.encode(), hashlib.sha256).hexdigest()
        headers = {
            "x-api-key": self.API_KEY,
            "x-api-timestamp": ts,
            "x-api-signature": signature,
            "Content-Type": "application/json"
        }
        return headers
    
    def get_order_status(self, order_id: str = None, client_order_id: str = None):
        """
        주문 상태 조회 – 특정 order_id 또는 clientOrderId 로
        :return: dict 응답, 필드에 state 또는 status 등이 포함됨
        """
        path = f"/v1/order/{order_id}"  # 실제 문서에서 “Get orders” endpoint path
        url = self.BASE_URL + path
        
        
        
        # 인증 필요
        headers = self._get_auth_headers("GET", path, body="")
        
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        j = resp.json()
        
        if not j.get("success", False):
            raise Exception(f"Woox order status 조회 실패: {j}")
        
        j = resp.json()
        if not j.get("success", False):
            raise Exception(f"Woox Get Order 실패: {j}")
        return j
    
    
    
    def checking_order_filled(self, order_id: str, side: str, size: float, price: float):
        """
        주문이 체결(filled)되었는지 확인
        side, size, price 인자는 참고용
        """
        try:
            order_info = self.get_order_status(order_id=order_id)
            if order_info is None:
                print("❌ 주문 정보 없음")
                return False
            
            status = order_info.get("status") or order_info.get("state")  # 문서에 status임 :contentReference[oaicite:8]{index=8}
            filled_size = float(order_info.get("executed", "0"))
            orig_size = float(order_info.get("quantity", "0"))
            
            
            print(f"주문 상태: {status}, 체결된 양: {filled_size}/{orig_size}")
            
            if status.upper() == "FILLED" and filled_size >= orig_size:
                print(f"[{side.upper()}] 주문 100% 체결 완료")
                return True
            else:
                print(f"[{side.upper()}] 미체결 또는 부분 체결 존재")
                return False
        except Exception as e:
            print("🔴 주문 조회 중 오류:", e)
            return False
    
   
    
    def get_last_trade_price(self, symbol: str):
        """
        최근 체결된 거래의 가격(마지막 거래가)을 가져옴
        """
        url = f"{self.BASE_URL}/v1/public/market_trades"
        params = {"symbol": symbol, "limit": 1}  # limit=1이면 가장 최근 1건
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        j = resp.json()
        if not j.get("success", False):
            return None
        trades = j.get("rows") or j.get("data") or []
        if not trades:
            return None
        # trades[0] 예: {"executed_price":0.0512,"executed_quantity":100,"side":"BUY",...}
        return float(trades[0].get("executed_price"))
            
    def get_orderbook(self, symbol: str, limit: int = 1):
        """
        시장의 호가 스냅샷 정보를 가져옴
        :param symbol: 예: "SPOT_ADP_USDT"
        :param limit: 각 side (bids/asks)에서 몇 개 가져올지
        :return: dict { 'best_bid': float, 'best_ask': float, 'bids': [...], 'asks': [...] }
        """
        
        url = f"{self.BASE_URL}/v1/public/orderbook/{symbol}"
        params = {"limit": limit}
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        j = resp.json()
        if not j.get("success", False):
            return {}
        
        bids = j.get("bids", [])
        asks = j.get("asks", [])

        if not bids or not asks:
            return {}

        best_bid = float(bids[0].get("price"))  # 가장 높은 매수 가격
        best_ask = float(asks[0].get("price"))  # 가장 낮은 매도 가격

        return {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "bids": bids,
            "asks": asks
        }

            
    def get_mid_price(self):        
        try:            
            res = self.get_orderbook(symbol=self.symbol, limit=10)
                        
            bids = res.get("best_bid", [])
            asks = res.get("best_ask", [])
            
            if not bids or not asks:
                raise Exception("호가 정보 없음")
            
            if not res:
                raise Exception(f"woox API Error: {res.get('message')}")

            

            self.best_bid = float(res.get("best_bid"))
            self.best_ask = float(res.get("best_ask"))
            #self.mid_price = (self.best_bid + self.best_ask) / 2
            
            msg = f"🟢 최고 매수: {self.best_bid} / 최저 매도: {self.best_ask}"
            self.status_label.config(text=msg, fg="green")            
            
        except Exception as e:
            print("오류 발생:", e)
            self.status_label.config(text="❌ GRND_USDT 호가 정보 오류", fg="gray")
            
            last_price =self.get_last_trade_price(symbol=self.symbol)
            if last_price:
                print("최근 체결가:", last_price)
                self.best_bid = float(last_price)
                self.best_ask = float(last_price)
                
                msg = f"🟢 최고 매수: {self.best_bid} / 최저 매도: {self.best_ask}"
                self.status_label.config(text=msg, fg="green")    
                
            else:
                print("최근 체결 내역 없음")

    def submit_orders(self,side, size, price):                
        
        spotAPI = APISpot(self.API_KEY, self.API_SECRET, self.API_MEMO, timeout=(3, 10))        
        response = spotAPI.post_submit_order(
            symbol=self.symbol,     # 거래쌍
            side=side,            # 'buy' 또는 'sell'
            type='limit',    # 주문 유형 ('limit' 또는 'market')
            size=size,         # 수량 (ADP 개수)
            price=price        # 가격 (USDT 기준)
        )  
        
        order_info = response[0]  # [0]은 응답에서 실제 데이터만 추출                
        if not order_info or  order_info.get("code")!= 1000:
            return None
            
        #response[0]['data']['order_id']
        order_id = order_info.get("data").get("order_id")

        # 주문 내용 확인
        print(f"[{side}] 주문 요청 - Price: {price}, Size: {size}, Order ID: {order_id}")          

        return order_id
    
    def cheking_orders(self,order_id,side, size, price):
        # 체결 여부 확인
        spotAPI = APISpot(self.API_KEY, self.API_SECRET, self.API_MEMO, timeout=(3, 10))        
        result = spotAPI.v4_query_order_by_id(order_id=order_id, query_state="history")[0]
        
        if not result or not result.get("success"):
            print("❌ 주문 조회 실패:", result)
            return False

        data = result.get("data", {})
        if not data or "order" not in data:
            print("❌ 주문 정보 없음", result)
            return False

        state = data.get("state", {})

        print(f"거래완료체크{result}")

        if state == 'filled':
            print(f"[{side.upper()}] 주문 100% 체결 완료")
            return True
        else:
            print(f"[{side.upper()}] 미체결 수량 존재")
            return False
        
    def _generate_signature(self,data):
        key = self.API_SECRET#'key' # Defined as a simple string.
        key_bytes= bytes(key , 'utf-8') # Commonly 'latin-1' or 'utf-8'
        data_bytes = bytes(data, 'utf-8') # Assumes `data` is also a string.
        return hmac.new(key_bytes, data_bytes , hashlib.sha256).hexdigest()

    def place_order(self, symbol: str, side: str,  quantity: str = None, price: str = None, ):
        milliseconds_since_epoch = round(datetime.now().timestamp() * 1000)
        
        headers = {
            'x-api-timestamp': str(milliseconds_since_epoch),
            'x-api-key': str(self.API_KEY),
            'x-api-signature': self._generate_signature(f"order_price={price}&order_quantity={quantity}&order_type=LIMIT&side={side}&symbol={symbol}|"+str(milliseconds_since_epoch)),
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
        data = response.json()
        if data.get('success', True):
            if data.get('order_id'):
                return data.get('order_id')
        
        return None
    
        

    def run_schedule(self, mode):
        errorMsg = ""
        while self.running:
            try:                          
                errorMsg = ""      
                price = random.uniform(self.best_bid, self.best_ask)                                
                maxAmount = random.uniform(int(self.amount_min_entry.get()), int(self.amount_max_entry.get()))
                size = round(maxAmount / price,2)      #  수량 (소수점 2자리로 제한)                                  
                price = format_price(price) #소수점 자리수 변경
    
            
                orderid = None
                if mode < random.randint(1, 100):             
                    
                    orderid = self.place_order(                
                        'SPOT_GRND_USDT',     # 거래쌍                
                        'SELL',            # 'buy' 또는 'sell'
                        #order_type='limit',    # 주문 유형 ('limit' 또는 'market')
                        size,         # 수량 (GRND 개수)
                        price        # 가격 (USDT 기준)
                    )                     
                    #orderid =self.submit_orders('sell', size, price)                                        
                    if None == orderid:
                        errorMsg ="주문 실패"
                        print(f"주문 실패: sell size: {size} price : {price}")
                        break
                    
                    orderid = self.place_order(                
                        'SPOT_GRND_USDT',     # 거래쌍                
                        'BUY',            # 'buy' 또는 'sell'
                        #order_type='limit',    # 주문 유형 ('limit' 또는 'market')
                        size,         # 수량 (GRND 개수)
                        price        # 가격 (USDT 기준)
                    )
                    #orderid = self.submit_orders('buy', size, price)
                    time.sleep(2)
                                        
                    #if False == self.cheking_orders(orderid,'buy', size, price):
                    if False == self.checking_order_filled(orderid,'buy', size, price):
                        errorMsg ="미 체결"
                        print(f"미 체결: sell->buy size: {size} price : {price}")
                    
                    print(f'[{mode}%]buy, {price}, {size}')
                    print(f'[{mode}%]sell, {price}, {size}')
                    
                else:                    
                    #orderid = self.submit_orders('buy', size, price)                                        
                    orderid = self.place_order(                
                        'SPOT_GRND_USDT',     # 거래쌍                
                        'BUY',            # 'buy' 또는 'sell'
                        #order_type='limit',    # 주문 유형 ('limit' 또는 'market')
                        size,         # 수량 (GRND 개수)
                        price        # 가격 (USDT 기준)
                    )               
                    if None == orderid:
                        errorMsg ="주문 실패"
                        print(f"주문 실패: buy size: {size} price : {price}")
                        break
                                        
                    #orderid = self.submit_orders('sell', size, price)
                    orderid = self.place_order(                
                        'SPOT_GRND_USDT',     # 거래쌍                
                        'SELL',            # 'buy' 또는 'sell'
                        #order_type='limit',    # 주문 유형 ('limit' 또는 'market')
                        size,         # 수량 (GRND 개수)
                        price        # 가격 (USDT 기준)
                    )               
                    
                    time.sleep(2)
                    #if False == self.cheking_orders(orderid,'sell', size, price):
                    if False == self.checking_order_filled(orderid,'sell', size, price):                
                        errorMsg ="미 체결"
                        print(f"미 체결: buy->sell size: {size} price : {price}")
                        
                    print(f'[{mode}%] sell, {price}, {size}')
                    print(f'[{mode}%]buy, {price}, {size}')
                                        
                
                t_min = int(self.time_min_entry.get())
                t_max = int(self.time_max_entry.get())
                wait_time = random.randint(t_min, t_max)                
                next_time = datetime.now() + timedelta(seconds=wait_time)
                self.root.title(f"VRA - [{mode}%] 다음 스케쥴 시간 {next_time.strftime('%H:%M:%S')}")                
                print(f"VRA - [{mode}%] 다음 스케쥴 시간 {next_time.strftime('%H:%M:%S')}")

                time.sleep(wait_time)
                
            except ValueError as e :
                msg = f"오류 {e}"
                print(msg)
                self.error_label.status_label.config(text=f"[오류중지]:{errorMsg}", fg="red")
                self.stop_bot()
                break
            
        if len(errorMsg):
            self.error_label.config(text=f"[오류중지]:{errorMsg}", fg="red")
        self.stop_bot()
            


if __name__ == "__main__":
    root = tk.Tk()
    app = BithumbBotGUI(root)
    root.mainloop()
