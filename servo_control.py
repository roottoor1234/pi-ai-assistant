import serial
import time

# Σύνδεση με το Arduino (προσαρμόσε τη θύρα αν χρειάζεται)
ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=1)
time.sleep(2)  # δώσε λίγο χρόνο στο Nano να κάνει reset

print("Connected. Type for example: '1 120' or '2 45'. Type 'q' to quit.\n")

while True:
    cmd = input("Servo & angle: ")  # π.χ. 1 120
    if cmd.lower() == 'q':
        break

    # έλεγξε ότι είναι σωστή μορφή (δύο αριθμοί χωρισμένοι με κενό)
    parts = cmd.strip().split()
    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
        ser.write((cmd + "\n").encode())  # στείλε στο Arduino
        print("-> Sent:", cmd)
        response = ser.readline().decode().strip()
        if response:
            print("<-", response)
    else:
        print("⚠️ Δώσε δύο αριθμούς: π.χ. '1 90' ή '2 45'")

ser.close()
print("Serial closed.")
