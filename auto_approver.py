import time
import sys
import os

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="ignore")

try:
    import uiautomation as auto
except ImportError:
    auto = None

try:
    import pyautogui
except ImportError:
    pyautogui = None

# Bosilishi kerak bo'lgan tugmalar matnlari
TARGET_BUTTONS = [
    "Always Allow",
    "Allow",
    "Accept",
    "Accept All",
    "Ruxsat berish",
    "Doim ruxsat berish",
    "Qabul qilish",
    "Run",
    "Proceed",
    "Confirm"
]

def find_and_click_buttons():
    """Windows UI daraxtidan kerakli tugmalarni qidirib avtomatik bosadi."""
    if not auto:
        return False
        
    clicked = False
    try:
        # Antigravity yoki faol oynani qidiramiz
        root = auto.GetRootControl()
        for btn_name in TARGET_BUTTONS:
            # Tugmani Name yoki Substring orqali qidirish
            btn = auto.ButtonControl(searchFromControl=root, searchDepth=15, SubName=btn_name)
            if btn.Exists(maxSearchSeconds=0.1):
                try:
                    # Tugma ekranda ko'rinayotgan bo'lsa
                    rect = btn.BoundingRectangle
                    if rect.width() > 0 and rect.height() > 0:
                        btn.Click(simulateMove=False)
                        print(f"[{time.strftime('%H:%M:%S')}] ✅ '{btn.Name}' tugmasi avtomatik bosildi!")
                        clicked = True
                        time.sleep(0.3)
                except Exception:
                    pass
    except Exception:
        pass
    return clicked

def main():
    print("=" * 60)
    print("🚀 Antigravity Auto-Approver ishga tushdi!")
    print("Har qanday ruxsat / tasdiqlash so'rovi avtomatik qabul qilinadi.")
    print("To'xtatish uchun: Ctrl + C bosing")
    print("=" * 60)
    
    while True:
        try:
            find_and_click_buttons()
            time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n🛑 Auto-Approver to'xtatildi.")
            break
        except Exception as e:
            time.sleep(1)

if __name__ == "__main__":
    main()
