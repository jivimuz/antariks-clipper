"""
Visual demo script for license expiry notification feature
This script simulates the UI behavior with different license states
"""
import json
from datetime import date, timedelta
from pathlib import Path

def print_box(title, content, color=""):
    """Print a styled box with title and content"""
    width = 70
    colors = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "blue": "\033[94m",
        "reset": "\033[0m"
    }
    
    c = colors.get(color, "")
    reset = colors["reset"] if c else ""
    
    print(f"{c}╔{'═' * width}╗{reset}")
    print(f"{c}║ {title.center(width-2)} ║{reset}")
    print(f"{c}╠{'═' * width}╣{reset}")
    for line in content:
        padding = width - len(line) - 2
        print(f"{c}║ {line}{' ' * padding} ║{reset}")
    print(f"{c}╚{'═' * width}╝{reset}")
    print()

def simulate_license_check(days_offset, scenario_name):
    """Simulate a license check scenario"""
    print("\n" + "="*80)
    print(f"SCENARIO: {scenario_name}")
    print("="*80 + "\n")
    
    # Calculate expiry date
    expiry_date = (date.today() + timedelta(days=days_offset)).strftime("%Y-%m-%d")
    
    # Simulate license data
    if days_offset < 0:
        # Expired
        print_box(
            "🚪 AUTO-LOGOUT TRIGGERED",
            [
                "❌ License Check Failed",
                "",
                f"License expired on: {expiry_date}",
                f"Days past expiry: {abs(days_offset)}",
                "",
                "Action taken:",
                "  • User logged out automatically",
                "  • Token removed from localStorage",
                "  • Redirected to /login page",
                "",
                "Toast message shown:",
                '  🔴 "Lisensi Anda telah berakhir."',
            ],
            "red"
        )
    elif days_offset < 3:
        # Expiring soon
        days_text = "hari ini" if days_offset == 0 else ("besok" if days_offset == 1 else f"{days_offset} hari lagi")
        
        print_box(
            "⚠️  LICENSE EXPIRING SOON",
            [
                "✅ License Status: Valid (but expiring soon)",
                "",
                f"Expires on: {expiry_date}",
                f"Days remaining: {days_offset}",
                "",
                "Warning toast shown:",
                f'  ⚠️  "Lisensi Anda akan berakhir {days_text}."',
                '      "Segera perpanjang lisensi Anda."',
                "",
                "User experience:",
                "  • Can continue using the app normally",
                "  • Warning shown on every page load",
                "  • Notification duration: 8 seconds",
            ],
            "yellow"
        )
    else:
        # Valid and not expiring soon
        print_box(
            "✅ LICENSE VALID",
            [
                "✅ License Status: Valid",
                "",
                f"Expires on: {expiry_date}",
                f"Days remaining: {days_offset}",
                "",
                "User experience:",
                "  • No warnings or notifications",
                "  • Full access to all features",
                "  • Silent background check",
            ],
            "green"
        )
    
    # Show license badge display
    if days_offset >= 0:
        print_box(
            "📱 UI DISPLAY - License Badge (Top Left)",
            [
                "┌─────────────────────────────────────┐",
                "│ 🛡️  Test User                       │",
                f"│ Expires: {expiry_date}              │",
                "└─────────────────────────────────────┘",
            ],
            "blue"
        )

def main():
    """Run all demo scenarios"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + "LICENSE EXPIRY NOTIFICATION - VISUAL DEMO".center(78) + "║")
    print("║" + "Antariks Clipper".center(78) + "║")
    print("╚" + "═" * 78 + "╝")
    
    scenarios = [
        (7, "License Valid - 7 Days Remaining (No Warning)"),
        (5, "License Valid - 5 Days Remaining (No Warning)"),
        (2, "License Expiring Soon - 2 Days Remaining ⚠️"),
        (1, "License Expiring Soon - 1 Day Remaining ⚠️"),
        (0, "License Expires Today ⚠️"),
        (-1, "License Expired - Auto Logout 🚪"),
    ]
    
    for days, scenario in scenarios:
        simulate_license_check(days, scenario)
        input("\nPress Enter to continue to next scenario...")
    
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + "DEMO COMPLETE ✅".center(78) + "║")
    print("║" + "".center(78) + "║")
    print("║" + "Key Features Demonstrated:".center(78) + "║")
    print("║" + "1. Early warning system (< 3 days)".center(78) + "║")
    print("║" + "2. Automatic logout on expiry".center(78) + "║")
    print("║" + "3. Clear user notifications".center(78) + "║")
    print("║" + "4. Non-intrusive when valid".center(78) + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n")

if __name__ == "__main__":
    main()
