yimport time
import hmac
import hashlib
import requests
import json

class AdvancedGridBot:
    def __init__(self, api_key, api_secret, demo_mode=False, starting_balance=1_000_000):
        self.api_key = api_key
        self.api_secret = api_secret.encode()
        self.demo_mode = demo_mode
        self.balance = starting_balance if demo_mode else 0
        self.position = 0
        self.grid_spacing = 0.008  # 0.8%
        self.trade_fraction = 0.25  # 25%
        self.profit = 0
        self.last_price = None
        self.trade_history = []

    def _get_kraken_signature(self, urlpath, data, nonce):
        postdata = (nonce + data).encode()
        sha256 = hashlib.sha256(postdata).digest()
        message = urlpath.encode() + sha256
        mac = hmac.new(base64.b64decode(self.api_secret), message, hashlib.sha512)
        sigdigest = mac.digest()
        return base64.b64encode(sigdigest).decode()

    def _kraken_request(self, method, endpoint, data=None):
        url = f"https://api.kraken.com{endpoint}"
        headers = {}
        if method == 'POST':
            nonce = str(int(time.time()*1000))
            data = data or {}
            data['nonce'] = nonce
            postdata = '&'.join([f"{k}={v}" for k,v in data.items()])
            headers = {
                'API-Key': self.api_key,
                'API-Sign': self._get_kraken_signature(endpoint, postdata, nonce)
            }
            response = requests.post(url, headers=headers, data=data)
        else:
            response = requests.get(url, params=data)
        return response.json()

    def get_market_price(self, pair="SOLUSD"):
        if self.demo_mode:
            # Simulate price movement for demo mode
            import random
            if self.last_price is None:
                self.last_price = 100  # arbitrary start price
            change_percent = random.uniform(-0.015, 0.015)
            self.last_price *= (1 + change_percent)
            return round(self.last_price, 2)
        else:
            # Real market price from Kraken
            endpoint = "/0/public/Ticker"
            params = {"pair": pair}
            resp = requests.get(f"https://api.kraken.com{endpoint}", params=params).json()
            try:
                price = float(resp['result'][list(resp['result'].keys())[0]]['c'][0])
                self.last_price = price
                return price
            except Exception as e:
                print("Error fetching price:", e)
                return None

    def place_order(self, price, side, volume):
        if self.demo_mode:
            # Simulate order fill immediately
            if side == "buy":
                cost = price * volume
                if cost > self.balance:
                    print("Insufficient balance for buy")
                    return False
                self.position += volume
                self.balance -= cost
                self.trade_history.append(f"Demo BUY {volume} at {price}")
            elif side == "sell":
                if volume > self.position:
                    print("Insufficient position to sell")
                    return False
                proceeds = price * volume
                self.position -= volume
                self.balance += proceeds
                self.profit += proceeds - (volume * price * (1 - self.grid_spacing))  # approximate profit
                self.trade_history.append(f"Demo SELL {volume} at {price}")
            return True
        else:
            # Real Kraken order placement (simplified market order)
            endpoint = "/0/private/AddOrder"
            volume_str = f"{volume:.8f}"
            data = {
                "pair": "SOLUSD",
                "type": side,
                "ordertype": "market",
                "volume": volume_str
            }
            resp = self._kraken_request('POST', endpoint, data)
            if resp.get("error"):
                print("Order error:", resp["error"])
                return False
            self.trade_history.append(f"LIVE {side.upper()} {volume} at {price}")
            return True

    def run(self, iterations=100):
        print("Starting Advanced Grid Bot...")
        # Seven Truths: 1. The market moves in polarity, ebb and flow.

        if self.last_price is None:
            self.last_price = self.get_market_price()

        for i in range(iterations):
            price = self.get_market_price()
            if price is None:
                time.sleep(1)
                continue

            # Seven Truths: 2. Timing is all about fees and execution speed.

            if self.position == 0:
                volume_to_buy = (self.balance * self.trade_fraction) / price
                self.place_order(price, "buy", volume_to_buy)
                self.last_price = price
            else:
                # If price increased enough, sell to lock profit before reversal
                if price >= self.last_price * (1 + self.grid_spacing):
                    self.place_order(price, "sell", self.position)
                    self.last_price = price
                # If price drops more than grid spacing, add to position to lower average cost
                elif price <= self.last_price * (1 - self.grid_spacing):
                    volume_to_buy = (self.balance * self.trade_fraction) / price
                    self.place_order(price, "buy", volume_to_buy)
                    self.last_price = price

            # Seven Truths: 3. Always lock profit before reversal.

            print(f"Iter {i+1}: Price={price:.2f}, Balance={self.balance:.2f}, Position={self.position:.4f}")

            # Intelligent profit rollover:
            # Reinvest all profits automatically by adding to balance if in demo

            if self.demo_mode:
                total_assets = self.balance + self.position * price
                self.balance = total_assets  # rollover all profit
                self.position = 0

            time.sleep(0.1)

        print("Final status:")
        print(f"Balance: {self.balance:.2f}")
        print(f"Position: {self.position:.4f}")
        print(f"Profit: {self.profit:.2f}")
        print("Trade History:")
        for t in self.trade_history:
            print(t)


if __name__ == "__main__":
    # Replace with your Kraken API keys or keep demo_mode=True to test without keys
    API_KEY = ""
    API_SECRET = ""
    bot = AdvancedGridBot(API_KEY, API_SECRET, demo_mode=True)
    bot.run()
        total_trades = len(self.trade_history)
        total_buys = sum(1 for t in self.trade_history if "BUY" in t)
        total_sells = sum(1 for t in self.trade_history if "SELL" in t)
        avg_buy_price = (
            sum(float(t.split("at")[1]) for t in self.trade_history if "BUY" in t) / total_buys
            if total_buys > 0 else 0
        )
        roi = ((self.balance - 1_000_000) / 1_000_000) * 100 if self.demo_mode else 0

        print(f"\nPerformance Summary:")
        print(f"Total Trades: {total_trades}")
        print(f"Buys: {total_buys}, Sells: {total_sells}")
        print(f"Average Buy Price: {avg_buy_price:.2f}")
        print(f"Return on Investment (ROI): {roi:.2f}%")
if __name__ == "__main__":
    # Replace with your Kraken API keys or keep demo_mode=True to test without keys
    API_KEY = ""
    API_SECRET = ""
    bot = AdvancedGridBot(API_KEY, API_SECRET, demo_mode=True)
    bot.run()

    # Moved these lines back to column 0
    total_trades = len(bot.trade_history)
    total_buys = sum(1 for t in bot.trade_history if "BUY" in t)
    total_sells = sum(1 for t in bot.trade_history if "SELL" in t)
    avg_buy_price = (
        sum(float(t.split("at")[1]) for t in bot.trade_history if "BUY" in t) / total_buys
        if total_buys > 0 else 0
    )
    roi = ((bot.balance - 1_000_000) / 1_000_000) * 100 if bot.demo_mode else 0

    print(f"\nPerformance Summary:")
    print(f"Total Trades: {total_trades}")
    print(f"Buys: {total_buys}, Sells: {total_sells}")
    print(f"Average Buy Price: {avg_buy_price:.2f}")
    print(f"Return on Investment (ROI): {roi:.2f}%")
