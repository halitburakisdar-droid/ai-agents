"""
Agent 1: Price Monitor
Model: qwen3.5:0.8b (LLM çağrısı yok - saf Python mantığı)
Görev: Altın/gümüş fiyatlarını izle, %2+ değişimde alarm ver
"""

import random
from datetime import datetime


class PriceMonitorAgent:
    NAME = "Price Monitor"
    MODEL = "qwen3.5:0.8b (mantık katmanı)"

    BASE = {"gold": 3150.00, "silver": 32.50}  # USD baz fiyatlar

    def run(self) -> dict:
        print(f"\n{'─'*50}")
        print(f"  Agent 1: {self.NAME}")
        print(f"{'─'*50}")

        # Önceki fiyatlar (bir önceki periyot)
        prev = {
            "gold":   round(self.BASE["gold"]   * (1 + random.uniform(-0.04, 0.04)), 2),
            "silver": round(self.BASE["silver"] * (1 + random.uniform(-0.04, 0.04)), 2),
        }

        # Güncel fiyatlar
        curr = {
            "gold":   round(self.BASE["gold"]   * (1 + random.uniform(-0.04, 0.04)), 2),
            "silver": round(self.BASE["silver"] * (1 + random.uniform(-0.04, 0.04)), 2),
        }

        # Değişim hesapla ve alarm üret
        changes = {}
        alarms = []
        for metal in curr:
            pct = (curr[metal] - prev[metal]) / prev[metal] * 100
            changes[metal] = round(pct, 2)
            icon = "📈" if pct > 0 else "📉"
            print(f"  {icon} {metal.upper():8s}: ${curr[metal]:>8.2f}  ({pct:+.2f}%)")
            if abs(pct) >= 2.0:
                alarms.append({
                    "metal": metal,
                    "change_pct": round(pct, 2),
                    "direction": "YÜKSELDİ" if pct > 0 else "DÜŞTÜ",
                    "prev": prev[metal],
                    "curr": curr[metal],
                })

        if alarms:
            print(f"\n  🚨 {len(alarms)} ALARM tetiklendi!")
            for a in alarms:
                print(f"     ⚡ {a['metal'].upper()} %{a['change_pct']:+.2f} {a['direction']}")
        else:
            print("\n  ✅ Alarm yok — değişimler %2 altında")

        return {
            "agent": self.NAME,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "prices": curr,
            "prev_prices": prev,
            "changes": changes,
            "alarms": alarms,
            "alarm_count": len(alarms),
        }
