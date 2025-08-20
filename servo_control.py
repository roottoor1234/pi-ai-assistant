import serial, time

ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=1)
time.sleep(2)  # δώσε λίγο χρόνο στο Nano

while True:
    angle = input("Give angle (0-180 or q to quit): ")
    if angle.lower() == 'q':
        break
    if angle.isdigit():
        ser.write((angle + "\n").encode())
        print("-> Sent:", angle)
        print("<-", ser.readline().decode().strip())

ser.close()
