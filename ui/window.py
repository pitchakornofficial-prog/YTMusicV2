import tkinter as tk
from tkinter import ttk


class MusicWindow:

    def __init__(self, state):

        self.state = state

        self.root = tk.Tk()
        self.root.title("TYMusicV2")
        self.root.geometry("800x560")
        self.root.minsize(700, 480)

        self.root.configure(bg="#121212")

        # -------------------------------------------------
        # Variables
        # -------------------------------------------------

        self.title_var = tk.StringVar(
            value="No music"
        )

        self.artist_var = tk.StringVar(
            value="Unknown artist"
        )

        self.album_var = tk.StringVar(
            value="Unknown album"
        )

        self.source_var = tk.StringVar(
            value="Source: Unknown"
        )

        self.current_time_var = tk.StringVar(
            value="0:00"
        )

        self.duration_var = tk.StringVar(
            value="0:00"
        )

        self.bluetooth_var = tk.StringVar(
            value="Bluetooth: Unknown"
        )

        self.playback_var = tk.StringVar(
            value="PAUSED"
        )

        self.lyric_var = tk.StringVar(
            value="Waiting for lyrics..."
        )

        # -------------------------------------------------
        # Style
        # -------------------------------------------------

        style = ttk.Style()

        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Music.Horizontal.TProgressbar",
            troughcolor="#282828",
            background="#ffffff",
            bordercolor="#282828",
            lightcolor="#ffffff",
            darkcolor="#ffffff",
            thickness=8
        )

        # -------------------------------------------------
        # Build
        # -------------------------------------------------

        self.build_ui()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close
        )

        self.update_ui()

    # =====================================================
    # Build UI
    # =====================================================

    def build_ui(self):

        main = tk.Frame(
            self.root,
            bg="#121212"
        )

        main.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=25
        )

        # =================================================
        # Header
        # =================================================

        header = tk.Frame(
            main,
            bg="#121212"
        )

        header.pack(
            fill="x"
        )

        logo = tk.Label(
            header,
            text="TYMusicV2",
            font=("Segoe UI", 20, "bold"),
            fg="white",
            bg="#121212"
        )

        logo.pack(
            side="left"
        )

        right_header = tk.Frame(
            header,
            bg="#121212"
        )

        right_header.pack(
            side="right"
        )

        self.playback_label = tk.Label(
            right_header,
            textvariable=self.playback_var,
            font=("Segoe UI", 9, "bold"),
            fg="white",
            bg="#282828",
            padx=10,
            pady=5
        )

        self.playback_label.pack(
            side="left",
            padx=(0, 10)
        )

        bluetooth = tk.Label(
            right_header,
            textvariable=self.bluetooth_var,
            font=("Segoe UI", 10),
            fg="#b3b3b3",
            bg="#121212"
        )

        bluetooth.pack(
            side="left"
        )

        # =================================================
        # Music
        # =================================================

        music_frame = tk.Frame(
            main,
            bg="#121212"
        )

        music_frame.pack(
            fill="x",
            pady=(30, 20)
        )

        # -------------------------------------------------
        # Album Art
        # -------------------------------------------------

        album = tk.Frame(
            music_frame,
            width=220,
            height=220,
            bg="#282828"
        )

        album.pack(
            side="left"
        )

        album.pack_propagate(False)

        album_label = tk.Label(
            album,
            text="♪",
            font=("Segoe UI", 72),
            fg="#777777",
            bg="#282828"
        )

        album_label.pack(
            expand=True
        )

        # -------------------------------------------------
        # Song Info
        # -------------------------------------------------

        info = tk.Frame(
            music_frame,
            bg="#121212"
        )

        info.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(30, 0)
        )

        title = tk.Label(
            info,
            textvariable=self.title_var,
            font=("Segoe UI", 26, "bold"),
            fg="white",
            bg="#121212",
            anchor="w",
            justify="left",
            wraplength=480
        )

        title.pack(
            fill="x",
            pady=(10, 5)
        )

        artist = tk.Label(
            info,
            textvariable=self.artist_var,
            font=("Segoe UI", 15),
            fg="#b3b3b3",
            bg="#121212",
            anchor="w"
        )

        artist.pack(
            fill="x"
        )

        album_name = tk.Label(
            info,
            textvariable=self.album_var,
            font=("Segoe UI", 11),
            fg="#777777",
            bg="#121212",
            anchor="w"
        )

        album_name.pack(
            fill="x",
            pady=(8, 20)
        )

        source = tk.Label(
            info,
            textvariable=self.source_var,
            font=("Segoe UI", 10, "bold"),
            fg="white",
            bg="#282828",
            padx=12,
            pady=6
        )

        source.pack(
            anchor="w"
        )

        # =================================================
        # Progress
        # =================================================

        progress_frame = tk.Frame(
            main,
            bg="#121212"
        )

        progress_frame.pack(
            fill="x",
            pady=(5, 20)
        )

        self.progress = ttk.Progressbar(
            progress_frame,
            orient="horizontal",
            mode="determinate",
            style="Music.Horizontal.TProgressbar",
            maximum=100
        )

        self.progress.pack(
            fill="x"
        )

        time_frame = tk.Frame(
            progress_frame,
            bg="#121212"
        )

        time_frame.pack(
            fill="x",
            pady=(6, 0)
        )

        current = tk.Label(
            time_frame,
            textvariable=self.current_time_var,
            font=("Segoe UI", 9),
            fg="#888888",
            bg="#121212"
        )

        current.pack(
            side="left"
        )

        duration = tk.Label(
            time_frame,
            textvariable=self.duration_var,
            font=("Segoe UI", 9),
            fg="#888888",
            bg="#121212"
        )

        duration.pack(
            side="right"
        )

        # =================================================
        # Lyrics
        # =================================================

        lyrics_frame = tk.Frame(
            main,
            bg="#121212"
        )

        lyrics_frame.pack(
            fill="both",
            expand=True,
            pady=(10, 0)
        )

        lyrics_title = tk.Label(
            lyrics_frame,
            text="CURRENT LYRICS",
            font=("Segoe UI", 9, "bold"),
            fg="#777777",
            bg="#121212"
        )

        lyrics_title.pack()

        lyric = tk.Label(
            lyrics_frame,
            textvariable=self.lyric_var,
            font=("Segoe UI", 22, "bold"),
            fg="white",
            bg="#121212",
            wraplength=700,
            justify="center"
        )

        lyric.pack(
            expand=True
        )

    # =====================================================
    # Update UI
    # =====================================================

    def update_ui(self):

        try:

            # -------------------------------------------------
            # Read state
            # -------------------------------------------------

            title = self.state.title
            artist = self.state.artist
            album = self.state.album
            source = self.state.source

            duration = self.state.duration

            lyrics = self.state.lyrics
            last_index = self.state.last_lyric_index

            position = self.state.display_position

            bluetooth_connected = (
                self.state.bluetooth_connected
            )

            playing = self.state.playing

            # -------------------------------------------------
            # Music information
            # -------------------------------------------------

            self.title_var.set(
                title if title else "No music"
            )

            self.artist_var.set(
                artist if artist else "Unknown artist"
            )

            self.album_var.set(
                album if album else "Unknown album"
            )

            self.source_var.set(
                f"Source: {source}"
            )

            # -------------------------------------------------
            # Playback state
            # -------------------------------------------------

            if playing:

                self.playback_var.set(
                    "PLAYING"
                )

            else:

                self.playback_var.set(
                    "PAUSED"
                )

            # -------------------------------------------------
            # Bluetooth
            # -------------------------------------------------

            if bluetooth_connected:

                self.bluetooth_var.set(
                    "Bluetooth: Connected"
                )

            else:

                self.bluetooth_var.set(
                    "Bluetooth: Disconnected"
                )

            # -------------------------------------------------
            # Position
            # -------------------------------------------------

            if duration > 0:

                position = max(
                    0.0,
                    min(
                        float(position),
                        float(duration)
                    )
                )

                percentage = (
                    position / duration
                ) * 100

                self.progress["value"] = percentage

            else:

                position = 0.0

                self.progress["value"] = 0

            # -------------------------------------------------
            # Time
            # -------------------------------------------------

            self.current_time_var.set(
                self.format_time(position)
            )

            self.duration_var.set(
                self.format_time(duration)
            )

            # -------------------------------------------------
            # Lyrics
            # -------------------------------------------------

            if (
                lyrics
                and
                0 <= last_index < len(lyrics)
            ):

                text = lyrics[last_index]["text"]

                self.lyric_var.set(
                    text
                )

            else:

                self.lyric_var.set(
                    "Waiting for lyrics..."
                )

        except Exception:
            pass

        # -----------------------------------------------------
        # Update every 100 ms
        # -----------------------------------------------------

        self.root.after(
            100,
            self.update_ui
        )

    # =====================================================
    # Helpers
    # =====================================================

    @staticmethod
    def format_time(seconds):

        try:
            seconds = int(seconds)
        except Exception:
            seconds = 0

        seconds = max(
            0,
            seconds
        )

        minutes = seconds // 60
        seconds = seconds % 60

        return f"{minutes}:{seconds:02d}"

    # =====================================================
    # Run
    # =====================================================

    def run(self):

        self.root.mainloop()

    # =====================================================
    # Close
    # =====================================================

    def close(self):

        self.root.destroy()