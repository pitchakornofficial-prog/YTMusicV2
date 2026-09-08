import asyncio
import threading

from core.app import main as core_main
from core.app import state
from ui.window import MusicWindow


def run_core():
    asyncio.run(core_main())


def main():

    # -------------------------------------------------
    # Start Core in background thread
    # -------------------------------------------------

    core_thread = threading.Thread(
        target=run_core,
        daemon=True
    )

    core_thread.start()

    # -------------------------------------------------
    # Tkinter MUST run in main thread
    # -------------------------------------------------

    window = MusicWindow(state)

    window.run()


if __name__ == "__main__":
    main()