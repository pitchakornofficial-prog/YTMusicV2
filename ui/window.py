import tkinter as tk
from tkinter import ttk
import io

from PIL import Image, ImageTk


class MusicWindow:

    def __init__(self, state):

        self.state = state

        self.root = tk.Tk()

        self.root.title("TYMusicV2")

        self.root.geometry("900x620")

        self.root.minsize(
            760,
            520
        )

        self.root.configure(
            bg="#121212"
        )

        # =================================================
        # Variables
        # =================================================

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
            value="SOURCE: UNKNOWN"
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

        # =================================================
        # Album art cache
        # =================================================

        self.album_image = None

        self.last_thumbnail = None

        # =================================================
        # Colors
        # =================================================

        self.bg = "#121212"

        self.panel = "#181818"

        self.card = "#242424"

        self.text = "#FFFFFF"

        self.secondary = "#B3B3B3"

        self.muted = "#777777"

        self.progress_bg = "#333333"

        self.progress_fg = "#FFFFFF"

        # =================================================
        # Style
        # =================================================

        self.setup_style()

        # =================================================
        # Build UI
        # =================================================

        self.build_ui()

        # =================================================
        # Close
        # =================================================

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close
        )

        # =================================================
        # Update
        # =================================================

        self.update_ui()

    # =====================================================
    # Style
    # =====================================================

    def setup_style(self):

        style = ttk.Style()

        try:

            style.theme_use(
                "clam"
            )

        except Exception:

            pass

        style.configure(
            "Music.Horizontal.TProgressbar",
            troughcolor=self.progress_bg,
            background=self.progress_fg,
            bordercolor=self.progress_bg,
            lightcolor=self.progress_fg,
            darkcolor=self.progress_fg,
            thickness=7
        )

    # =====================================================
    # Build UI
    # =====================================================

    def build_ui(self):

        main = tk.Frame(
            self.root,
            bg=self.bg
        )

        main.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=25
        )

        # =================================================
        # Header
        # =================================================

        header = tk.Frame(
            main,
            bg=self.bg
        )

        header.pack(
            fill="x"
        )

        logo = tk.Label(
            header,
            text="TYMusicV2",
            font=(
                "Segoe UI",
                21,
                "bold"
            ),
            fg=self.text,
            bg=self.bg
        )

        logo.pack(
            side="left"
        )

        status_frame = tk.Frame(
            header,
            bg=self.bg
        )

        status_frame.pack(
            side="right"
        )

        self.playback_label = tk.Label(
            status_frame,
            textvariable=self.playback_var,
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            fg=self.text,
            bg=self.card,
            padx=12,
            pady=6
        )

        self.playback_label.pack(
            side="left",
            padx=(0, 8)
        )

        self.bluetooth_label = tk.Label(
            status_frame,
            textvariable=self.bluetooth_var,
            font=(
                "Segoe UI",
                9
            ),
            fg=self.secondary,
            bg=self.bg
        )

        self.bluetooth_label.pack(
            side="left"
        )

        # =================================================
        # Music card
        # =================================================

        music_card = tk.Frame(
            main,
            bg=self.panel
        )

        music_card.pack(
            fill="x",
            pady=(28, 20)
        )

        # =================================================
        # Album Art
        # =================================================

        album_container = tk.Frame(
            music_card,
            width=250,
            height=250,
            bg=self.card
        )

        album_container.pack(
            side="left",
            padx=25,
            pady=25
        )

        album_container.pack_propagate(
            False
        )

        self.album_art = tk.Label(
            album_container,
            text="♪",
            font=(
                "Segoe UI",
                82,
                "normal"
            ),
            fg="#666666",
            bg=self.card
        )

        self.album_art.pack(
            expand=True
        )

        # =================================================
        # Information
        # =================================================

        info = tk.Frame(
            music_card,
            bg=self.panel
        )

        info.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(5, 30),
            pady=25
        )

        now_playing = tk.Label(
            info,
            text="NOW PLAYING",
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            fg=self.muted,
            bg=self.panel
        )

        now_playing.pack(
            anchor="w",
            pady=(5, 10)
        )

        self.title_label = tk.Label(
            info,
            textvariable=self.title_var,
            font=(
                "Segoe UI",
                25,
                "bold"
            ),
            fg=self.text,
            bg=self.panel,
            anchor="w",
            justify="left",
            wraplength=500
        )

        self.title_label.pack(
            fill="x",
            anchor="w"
        )

        artist = tk.Label(
            info,
            textvariable=self.artist_var,
            font=(
                "Segoe UI",
                16
            ),
            fg=self.secondary,
            bg=self.panel,
            anchor="w"
        )

        artist.pack(
            fill="x",
            pady=(8, 0)
        )

        album = tk.Label(
            info,
            textvariable=self.album_var,
            font=(
                "Segoe UI",
                11
            ),
            fg=self.muted,
            bg=self.panel,
            anchor="w"
        )

        album.pack(
            fill="x",
            pady=(5, 18)
        )

        source_frame = tk.Frame(
            info,
            bg=self.panel
        )

        source_frame.pack(
            anchor="w"
        )

        source_label = tk.Label(
            source_frame,
            textvariable=self.source_var,
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            fg=self.text,
            bg=self.card,
            padx=12,
            pady=6
        )

        source_label.pack()

        # =================================================
        # Progress
        # =================================================

        progress_section = tk.Frame(
            main,
            bg=self.bg
        )

        progress_section.pack(
            fill="x"
        )

        self.progress = ttk.Progressbar(
            progress_section,
            orient="horizontal",
            mode="determinate",
            maximum=100,
            style="Music.Horizontal.TProgressbar"
        )

        self.progress.pack(
            fill="x"
        )

        time_frame = tk.Frame(
            progress_section,
            bg=self.bg
        )

        time_frame.pack(
            fill="x",
            pady=(7, 0)
        )

        current_time = tk.Label(
            time_frame,
            textvariable=self.current_time_var,
            font=(
                "Segoe UI",
                9
            ),
            fg=self.secondary,
            bg=self.bg
        )

        current_time.pack(
            side="left"
        )

        duration = tk.Label(
            time_frame,
            textvariable=self.duration_var,
            font=(
                "Segoe UI",
                9
            ),
            fg=self.secondary,
            bg=self.bg
        )

        duration.pack(
            side="right"
        )

        # =================================================
        # Lyrics
        # =================================================

        lyrics_card = tk.Frame(
            main,
            bg=self.panel
        )

        lyrics_card.pack(
            fill="both",
            expand=True,
            pady=(22, 0)
        )

        lyrics_header = tk.Label(
            lyrics_card,
            text="CURRENT LYRICS",
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            fg=self.muted,
            bg=self.panel
        )

        lyrics_header.pack(
            pady=(15, 0)
        )

        self.lyric_label = tk.Label(
            lyrics_card,
            textvariable=self.lyric_var,
            font=(
                "Segoe UI",
                22,
                "bold"
            ),
            fg=self.text,
            bg=self.panel,
            wraplength=760,
            justify="center"
        )

        self.lyric_label.pack(
            fill="both",
            expand=True,
            padx=30
        )

    # =====================================================
    # Album Art
    # =====================================================

    def update_album_art(self, thumbnail):

        if not thumbnail:

            self.album_image = None

            self.last_thumbnail = None

            self.album_art.configure(
                image="",
                text="♪"
            )

            return

        if thumbnail == self.last_thumbnail:

            return

        try:

            self.last_thumbnail = thumbnail

            image = Image.open(
                io.BytesIO(thumbnail)
            )

            image = image.convert(
                "RGB"
            )

            # Make the image exactly fit the album-art box
            image = image.resize(
                (250, 250),
                Image.Resampling.LANCZOS
            )

            self.album_image = ImageTk.PhotoImage(
                image
            )

            self.album_art.configure(
                image=self.album_image,
                text=""
            )

        except Exception as e:

            print(
                f"Album art display error: {e}"
            )

            self.album_image = None

            self.last_thumbnail = None

            self.album_art.configure(
                image="",
                text="♪"
            )

    # =====================================================
    # Update UI
    # =====================================================

    def update_ui(self):

        try:

            title = self.state.title

            artist = self.state.artist

            album = self.state.album

            source = self.state.source

            thumbnail = getattr(
                self.state,
                "thumbnail",
                None
            )

            duration = self.state.duration

            lyrics = self.state.lyrics

            last_index = (
                self.state.last_lyric_index
            )

            position = (
                self.state.display_position
            )

            bluetooth_connected = (
                self.state.bluetooth_connected
            )

            playing = self.state.playing

            # =================================================
            # Album Art
            # =================================================

            self.update_album_art(
                thumbnail
            )

            # =================================================
            # Song information
            # =================================================

            if title:

                self.title_var.set(
                    title
                )

            else:

                self.title_var.set(
                    "No music"
                )

            if artist:

                self.artist_var.set(
                    artist
                )

            else:

                self.artist_var.set(
                    "Unknown artist"
                )

            if album:

                self.album_var.set(
                    album
                )

            else:

                self.album_var.set(
                    "Unknown album"
                )

            # =================================================
            # Source
            # =================================================

            if source:

                self.source_var.set(
                    f"SOURCE: {source.upper()}"
                )

            else:

                self.source_var.set(
                    "SOURCE: UNKNOWN"
                )

            # =================================================
            # Playback
            # =================================================

            if playing:

                self.playback_var.set(
                    "PLAYING"
                )

                self.playback_label.configure(
                    bg="#303030"
                )

            else:

                self.playback_var.set(
                    "PAUSED"
                )

                self.playback_label.configure(
                    bg="#242424"
                )

            # =================================================
            # Bluetooth
            # =================================================

            if bluetooth_connected:

                self.bluetooth_var.set(
                    "Bluetooth: Connected"
                )

            else:

                self.bluetooth_var.set(
                    "Bluetooth: Disconnected"
                )

            # =================================================
            # Progress
            # =================================================

            if duration > 0:

                position = max(
                    0.0,
                    min(
                        float(position),
                        float(duration)
                    )
                )

                percentage = (
                    position
                    / duration
                    * 100
                )

                self.progress["value"] = (
                    percentage
                )

            else:

                position = 0.0

                self.progress["value"] = 0

            # =================================================
            # Time
            # =================================================

            self.current_time_var.set(
                self.format_time(
                    position
                )
            )

            self.duration_var.set(
                self.format_time(
                    duration
                )
            )

            # =================================================
            # Lyrics
            # =================================================

            if (
                lyrics
                and
                0 <= last_index < len(lyrics)
            ):

                text = lyrics[
                    last_index
                ]["text"]

                if text:

                    self.lyric_var.set(
                        text
                    )

                else:

                    self.lyric_var.set(
                        "♪"
                    )

            else:

                self.lyric_var.set(
                    "Waiting for lyrics..."
                )

        except Exception:
            pass

        self.root.after(
            100,
            self.update_ui
        )

    # =====================================================
    # Format Time
    # =====================================================

    @staticmethod
    def format_time(seconds):

        try:

            seconds = int(
                seconds
            )

        except Exception:

            seconds = 0

        seconds = max(
            0,
            seconds
        )

        hours = seconds // 3600

        minutes = (
            seconds % 3600
        ) // 60

        seconds = (
            seconds % 60
        )

        if hours > 0:

            return (
                f"{hours}:"
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )

        return (
            f"{minutes}:"
            f"{seconds:02d}"
        )

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