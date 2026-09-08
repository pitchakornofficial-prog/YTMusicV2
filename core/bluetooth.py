import time
import threading

import serial
import serial.tools.list_ports


DEVICE_NAME = "TYMusicV2"

MAX_RETRIES = 0
RETRY_DELAY = 2.0

HANDSHAKE_TIMEOUT = 3.0

# ต้องส่งไม่สำเร็จติดต่อกันกี่ครั้ง
# จึงจะถือว่า Bluetooth หลุด
SEND_FAILURE_THRESHOLD = 3

# COM port ล่าสุดที่เชื่อมต่อสำเร็จ
last_port = None

# ป้องกัน serial operation ชนกัน
serial_lock = threading.RLock()


def find_bluetooth_ports():
    devices = []

    print("\nScanning Bluetooth COM ports...")

    try:
        ports = serial.tools.list_ports.comports()
    except Exception as e:
        print(f"Bluetooth scan error: {e}")
        return devices

    for port in ports:
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
        print(f"Connection failed: {port} - {e}")
        return None


def is_connected(connection):
    if not connection:
        return False

    try:
        return connection.is_open

    except Exception:
        return False


def send(connection, message):
    if not is_connected(connection):
        return False

    with serial_lock:
        try:
            connection.write(
                (message + "\n").encode("utf-8")
            )

            return True

        except (
            serial.SerialException,
            serial.SerialTimeoutException,
            OSError
        ) as e:

            print(f"Bluetooth send error: {e}")
            return False

        except Exception as e:

            print(f"Bluetooth send error: {e}")
            return False


def close(connection):
    if not connection:
        return

    with serial_lock:
        try:
            if connection.is_open:
                connection.close()

        except Exception as e:
            print(f"Bluetooth close error: {e}")


def handshake(connection):
    if not connection:
        return False

    with serial_lock:
        try:
            if not connection.is_open:
                return False

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

                        connection.reset_input_buffer()

                        return True

                time.sleep(0.05)

            print(
                f"Handshake timeout: {connection.port}"
            )

            return False

        except (
            serial.SerialException,
            serial.SerialTimeoutException,
            OSError
        ) as e:

            print(
                f"Handshake connection error: {e}"
            )

            return False

        except Exception as e:

            print(
                f"Handshake error: {e}"
            )

            return False


def try_port(port):
    global last_port

    connection = connect(port)

    if not connection:
        return None

    if handshake(connection):

        last_port = port

        print(
            f"\n{DEVICE_NAME} connected on {port}"
        )

        return connection

    close(connection)

    time.sleep(0.3)

    return None


def find_and_connect_once():
    global last_port

    devices = find_bluetooth_ports()

    if not devices:

        print("\nNo Bluetooth COM ports found.")

        return None

    print(
        f"\nFound {len(devices)} "
        f"Bluetooth COM port(s)."
    )

    ports = [
        device["port"]
        for device in devices
    ]

    # ---------------------------------------------
    # ลอง COM ล่าสุดก่อน
    # ---------------------------------------------

    if last_port and last_port in ports:

        print(
            f"\nTrying last successful port "
            f"{last_port} first..."
        )

        connection = try_port(last_port)

        if connection:
            return connection

        print(
            f"Last port {last_port} failed."
        )

    # ---------------------------------------------
    # ลอง COM อื่น
    # ---------------------------------------------

    for port in ports:

        if port == last_port:
            continue

        print(f"\nTrying {port}...")

        connection = try_port(port)

        if connection:
            return connection

    print(
        f"\n{DEVICE_NAME} not found in this scan."
    )

    return None


def find_and_connect():
    retry_count = 0

    while True:

        retry_count += 1

        print()
        print("==============================")
        print(
            f"Bluetooth connection attempt "
            f"#{retry_count}"
        )
        print("==============================")

        connection = find_and_connect_once()

        if connection:
            return connection

        if (
            MAX_RETRIES > 0
            and retry_count >= MAX_RETRIES
        ):

            print(
                "\nMaximum Bluetooth retries reached."
            )

            return None

        print(
            f"\nRetrying in "
            f"{RETRY_DELAY:.1f} seconds..."
        )

        time.sleep(RETRY_DELAY)


def reconnect(connection=None):
    print()
    print("==============================")
    print("Bluetooth reconnect")
    print("==============================")

    if connection:

        print(
            "Closing old Bluetooth connection..."
        )

        close(connection)

        time.sleep(0.7)

    new_connection = find_and_connect()

    if new_connection:

        print(
            f"\n{DEVICE_NAME} reconnected."
        )

        return new_connection

    print(
        f"\nUnable to reconnect to "
        f"{DEVICE_NAME}."
    )

    return None


# --------------------------------------------------
# Optional PING
# --------------------------------------------------
# เก็บไว้สำหรับทดสอบด้วยตัวเอง
# ระบบ reconnect หลักจะไม่ใช้ PING แล้ว
# --------------------------------------------------

def ping(connection, timeout=2.0):
    if not is_connected(connection):
        return False

    with serial_lock:
        try:

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

        except (
            serial.SerialException,
            serial.SerialTimeoutException,
            OSError
        ) as e:

            print(
                f"Bluetooth ping error: {e}"
            )

            return False

        except Exception as e:

            print(
                f"Bluetooth ping error: {e}"
            )

            return False


def test_connection(connection):
    if not is_connected(connection):
        return False

    return ping(connection)