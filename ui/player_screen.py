import customtkinter as ctk


class PlayerScreen:
    def __init__(self, master) -> None:

        self.frame = ctk.CTkFrame(master)
        self.song_label = ctk.CTkLabel(self.frame, text="No song playing")
        self.progress = ctk.CTkProgressBar(self.frame)
        self.song_label.pack(pady=12)
        self.progress.pack(fill="x", padx=16, pady=12)
