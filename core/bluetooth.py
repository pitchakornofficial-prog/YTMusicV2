import time
import threading

import serial
import serial.tools.list_ports


DEVICE_NAME = "TYMusicV2"

# Retry
MAX_RETRIES = 0
RETRY_DELAY = 2.0

# Handshake
HANDSHAKE_TIMEOUT = 3.0

# Send failure
SEND_FAILURE_THRESHOLD = 3

# Quiet reconnect settings
QUIET_AFTER_FAILURES = 3
MAX_RETRY_DELAY = 5.0


last_port = None
serial_lock = threading.RLock()

# ใช้เก็บสถานะล่าสุดเพื่อป้องกันการ print ซ้ำ
_last_scan_state = None
_last_error_state = None


def find_bluetooth_ports(verbose=False):
    """
    ค้นหา Bluetooth COM ports

    verbose=False:
        ไม่แสดง COM port ทุกครั้งที่ scan

    verbose=True:
        แสดงรายละเอียด COM port ทั้งหมด
    """

    global _last_scan_state

    devices = []

    try:
        ports = serial.tools.list_ports.comports()
    except Exception as e:
        if _last_error_state != str(e):
            print(f"Bluetooth scan error: {e}")
            _last_error_state = str(e)

        return devices

    for port in ports:
        description = port.description or ""
        manufacturer = port.manufacturer or ""

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

    # สถานะเปลี่ยน เช่น 0 -> 4 หรือ 4 -> 0
    current_state = tuple(
        device["port"]
        for device in devices
    )

    if verbose or current_state != _last_scan_state:
        if devices:
            print("\nBluetooth COM ports found:")

            for device in devices:
                print(
                    f"  {device['port']} | "
                    f"{device['name']} | "
                    f"{device['manufacturer']}"
                )
        else:
            if _last_scan_state is not None:
                print("\nBluetooth COM ports not available.")

        _last_scan_state = current_state

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
        # ไม่ print error เดิมซ้ำทุก retry
        global _last_error_state

        error_state = f"{port}: {e}"

        if error_state != _last_error_state:
            print(f"Connection failed: {port} - {e}")
            _last_error_state = error_state

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
            print(f"Handshake error: {e}")
            return False


def try_port(port):
    global last_port
    global _last_error_state

    connection = connect(port)

    if not connection:
        return None

    if handshake(connection):
        last_port = port

        # ล้าง error state
        _last_error_state = None

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
        return None

    ports = [
        device["port"]
        for device in devices
    ]

    # --------------------------------
    # Try last successful port first
    # --------------------------------

    if last_port and last_port in ports:

        print(
            f"\nTrying last successful port "
            f"{last_port}..."
        )

        connection = try_port(last_port)

        if connection:
            return connection

    # --------------------------------
    # Try other Bluetooth ports
    # --------------------------------

    for port in ports:

        if port == last_port:
            continue

        connection = try_port(port)

        if connection:
            return connection

    return None


def find_and_connect():
    """
    Initial connection / reconnect

    ทำงานแบบ quiet:
    - ไม่แสดง attempt number
    - ไม่ spam รายละเอียดทุก scan
    - เพิ่ม delay เมื่อ reconnect ไม่สำเร็จ
    """

    retry_count = 0
    retry_delay = RETRY_DELAY

    waiting_message_shown = False

    while True:

        retry_count += 1

        connection = find_and_connect_once()

        if connection:
            print(
                f"{DEVICE_NAME} connection successful."
            )

            return connection

        # --------------------------------
        # No Bluetooth device available
        # --------------------------------

        if not waiting_message_shown:
            print(
                "\nWaiting for Bluetooth device..."
            )

            waiting_message_shown = True

        time.sleep(retry_delay)

        # ค่อย ๆ เพิ่ม delay แต่ไม่เกิน MAX_RETRY_DELAY
        retry_delay = min(
            retry_delay + 0.5,
            MAX_RETRY_DELAY
        )

        # --------------------------------
        # Optional retry limit
        # --------------------------------

        if (
            MAX_RETRIES > 0
            and retry_count >= MAX_RETRIES
        ):
            print(
                "\nMaximum Bluetooth retries reached."
            )

            return None


def reconnect(connection=None):
    """
    Reconnect Bluetooth หลัง connection หลุด
    """

    global _last_scan_state
    global _last_error_state

    print()
    print("==============================")
    print("Bluetooth reconnect")
    print("==============================")

    # Reset quiet-state
    _last_scan_state = None
    _last_error_state = None

    # --------------------------------
    # Close old connection
    # --------------------------------

    if connection:

        print(
            "Closing old Bluetooth connection..."
        )

        close(connection)

        time.sleep(0.7)

    # --------------------------------
    # Search and reconnect
    # --------------------------------

    new_connection = find_and_connect()

    if new_connection:

        print(
            f"\n{DEVICE_NAME} reconnected."
        )

        return new_connection

    print(
        f"\nUnable to reconnect to {DEVICE_NAME}."
    )

    return None


def ping(connection, timeout=2.0):
    """
    Optional diagnostic only.
    ไม่ใช้เป็นตัวตัดสิน reconnect หลัก
    """

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