# === arduino_control.py ===
import serial
import time

# Ρύθμιση σειριακής επικοινωνίας
try:
    ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=1)
    time.sleep(2)
    print("✅ Arduino συνδέθηκε επιτυχώς.")
except Exception as e:
    ser = None
    print("⚠️ Δεν βρέθηκε Arduino:", e)


def send_command(command: str):
    """Στέλνει απλή εντολή μέσω serial στο Arduino."""
    if ser:
        try:
            ser.write((command + "\n").encode())
            print(f"➡️ Εστάλη: {command}")
        except Exception as e:
            print("⚠️ Σφάλμα κατά την αποστολή εντολής:", e)
    else:
        print("⚠️ Arduino δεν είναι συνδεδεμένο.")


def wave_left_hand():
    """Κινεί το αριστερό χέρι (για χειραψία ή χαιρετισμό)."""
    if not ser:
        print("⚠️ Arduino δεν είναι διαθέσιμο.")
        return
    print("👋 Εκτελείται χειραψία (αριστερό χέρι)...")
    send_command("2 60")   # π.χ. servo 2 -> 60°
    time.sleep(3)
    send_command("2 0")    # επαναφορά


def wave_right_hand():
    """Κινεί το δεξί χέρι (για χειραψία ή χαιρετισμό)."""
    if not ser:
        print("⚠️ Arduino δεν είναι διαθέσιμο.")
        return
    print("👋 Εκτελείται χειραψία (δεξί χέρι)...")
    send_command("1 60")   # π.χ. servo 1 -> 60°
    time.sleep(3)
    send_command("1 0")    # επαναφορά