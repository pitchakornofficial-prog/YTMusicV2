import time
import serial
import serial.tools.list_ports


DEVICE_NAME = "TYMusicV2"

# จำนวนครั้งที่ลองเชื่อมต่อใหม่
MAX_RETRIES = 0
# 0 = ลองไปเรื่อย ๆ จนกว่าจะเจอ

RETRY_DELAY = 2.0

HANDSHAKE_TIMEOUT = 3.0


# =========================================================
# Scan Bluetooth COM Ports
# =========================================================

def find_bluetooth_ports():
    devices = []

    print("\nScanning Bluetooth COM ports...")

    for port in serial.tools.list_ports.comports():

        description = port.description or ""
        manufacturer = port.manufacturer or ""

        print(
            f"Port: {port.device} | "
            f"Description: {description} | "
            f"Manufacturer: {manufacturer}"
        )

        text = f"{description} {manufacturer}".lower()

        if (
            "bluetooth" in text
            or "standard serial over bluetooth" in text
        ):
            devices.append({
                "port": port.device,
                "name": description,
                "manufacturer": manufacturer
            })

    return devices


# =========================================================
# Open COM Port
# =========================================================

def connect(port, baudrate=115200):

    try:

        connection = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=1,
            write_timeout=2
        )

        print(f"Connected: {port}")

        return connection

    except Exception as e:

        print(
            f"Connection failed: {port} - {e}"
        )

        return None


# =========================================================
# Send
# =========================================================

def send(connection, message):

    if not connection:
        return False

    try:

        if not connection.is_open:
            return False

        connection.write(
            (message + "\n").encode("utf-8")
        )

        return True

    except Exception as e:

        print(
            f"Bluetooth send error: {e}"
        )

        return False


# =========================================================
# Close
# =========================================================

def close(connection):

    if connection:

        try:

            if connection.is_open:
                connection.close()

        except Exception:
            pass


# =========================================================
# Handshake
# =========================================================

def handshake(connection):

    if not connection:
        return False

    try:

        # Clear old data
        connection.reset_input_buffer()
        connection.reset_output_buffer()

        print(
            f"Sending HELLO to {connection.port}..."
        )

        connection.write(b"HELLO\n")

        deadline = time.time() + HANDSHAKE_TIMEOUT

        while time.time() < deadline:

            if connection.in_waiting:

                line = connection.readline()

                response = line.decode(
                    "utf-8",
                    errors="ignore"
                ).strip()

                if response:

                    print(
                        f"{connection.port} -> {response}"
                    )

                if response == DEVICE_NAME:

                    print(
                        f"Handshake OK: {DEVICE_NAME}"
                    )

                    # Remove any remaining handshake data
                    connection.reset_input_buffer()

                    return True

            time.sleep(0.05)

        print(
            f"Handshake timeout: {connection.port}"
        )

        return False

    except Exception as e:

        print(
            f"Handshake error: {e}"
        )

        return False


# =========================================================
# Find and Connect Once
# =========================================================

def find_and_connect_once():

    devices = find_bluetooth_ports()

    if not devices:

        print(
            "\nNo Bluetooth COM ports found."
        )

        return None

    print(
        f"\nFound {len(devices)} Bluetooth COM port(s)."
    )

    for device in devices:

        port = device["port"]

        print(
            f"\nTrying {port}..."
        )

        connection = connect(port)

        if not connection:
            continue

        if handshake(connection):

            print(
                f"\n{DEVICE_NAME} connected on {port}"
            )

            return connection

        close(connection)

        # Give Windows Bluetooth SPP time to release
        time.sleep(0.5)

    print(
        f"\n{DEVICE_NAME} not found in this scan."
    )

    return None


# =========================================================
# Find and Connect with Automatic Retry
# =========================================================

def find_and_connect():

    retry_count = 0

    while True:

        retry_count += 1

        print()
        print("==============================")
        print(
            f"Bluetooth connection attempt #{retry_count}"
        )
        print("==============================")

        connection = find_and_connect_once()

        if connection:

            return connection

        if MAX_RETRIES > 0 and retry_count >= MAX_RETRIES:

            print(
                "\nMaximum Bluetooth retries reached."
            )

            return None

        print(
            f"\nRetrying in {RETRY_DELAY:.1f} seconds..."
        )

        time.sleep(RETRY_DELAY)


# =========================================================
# Ping ESP32
# =========================================================

def ping(connection, timeout=2.0):

    if not connection:
        return False

    try:

        if not connection.is_open:
            return False

        connection.reset_input_buffer()

        connection.write(b"PING\n")

        deadline = time.time() + timeout

        while time.time() < deadline:

            if connection.in_waiting:

                line = connection.readline()

                response = line.decode(
                    "utf-8",
                    errors="ignore"
                ).strip()

                if response == "PONG":

                    return True

            time.sleep(0.05)

        return False

    except Exception as e:

        print(
            f"Bluetooth ping error: {e}"
        )

        return False