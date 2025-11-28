"""
Coordinate Finder Tool
======================
Move your mouse to find exact coordinates of UI elements.
Press Ctrl+C to exit.
"""
import time
import pyautogui

print("""
╔══════════════════════════════════════════════════════════════╗
║           Coordinate Finder Tool                             ║
║                                                              ║
║  Move your mouse over the "New Note" button in CPRS          ║
║  The coordinates will be displayed in real-time              ║
║  Press Ctrl+C to exit                                        ║
╚══════════════════════════════════════════════════════════════╝
""")

try:
    while True:
        x, y = pyautogui.position()
        print(f"\rMouse position: x={x:4d}, y={y:4d}    ", end="", flush=True)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n\nFinal position captured!")
    x, y = pyautogui.position()
    print(f"Coordinates: ({x}, {y})")
    print("\nYou can use these in the demo script.")
