import time
from datetime import datetime

print("Price Monitor Agent BAŞLADI\n")

for i in range(1, 6):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"✅ Çalışıyorum - {timestamp}  (Döngü {i}/5)")
    if i < 5:
        time.sleep(3)

print("\nTamamlandı!")
