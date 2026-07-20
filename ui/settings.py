import customtkinter as ctk


class SettingsView:
    def __init__(self, master) -> None:

        self.frame = ctk.CTkFrame(master)
        self.camera_label = ctk.CTkLabel(self.frame, text="Camera")
        self.camera_label.pack(pady=12)
