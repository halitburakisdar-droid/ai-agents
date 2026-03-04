"""
Agent: Market Data — qwen3.5:0.8b (Python logic, LLM yok)
Altın/Gümüş/BTC/BIST sahte günlük fiyat verisi
"""
import random
from datetime import datetime


class MarketDataAgent:
    NAME = "Market Data"
    MODEL = "qwen3.5:0.8b (Python logic)"

    BASE = {
        "ALTIN":  3150.00,   # USD/oz
        "GUMUS":  32.50,     # USD/oz
        "BTC":    97000.00,  # USD
        "BIST100": 9850.00,  # TRY puan
        "DOLAR":  32.80,     # TRY
        "EURO":   35.60,     # TRY
    }

    def run(self) -> dict:
        print(f"  [{self.NAME}] Piyasa verileri alınıyor...")
        data = {}
        for sembol, baz in self.BASE.items():
            degisim = random.uniform(-0.05, 0.05)
            fiyat   = round(baz * (1 + degisim), 2)
            data[sembol] = {
                "fiyat":   fiyat,
                "degisim": round(degisim * 100, 2),
                "icon":    "📈" if degisim > 0 else "📉",
            }
            print(f"    {data[sembol]['icon']} {sembol:8s}: {fiyat:>10.2f}  ({degisim*100:+.2f}%)")

        # En çok kazanan / kaybeden
        sorted_d = sorted(data.items(), key=lambda x: x[1]["degisim"])
        winner   = sorted_d[-1]
        loser    = sorted_d[0]

        return {
            "agent":   self.NAME,
            "data":    data,
            "winner":  {"sembol": winner[0], **winner[1]},
            "loser":   {"sembol": loser[0],  **loser[1]},
            "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M"),
        }
