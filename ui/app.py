import customtkinter as ctk
import config
from ui.home import HomeView


class EmotionMusicApp:
    def __init__(self) -> None:
        self.window = None
        self.home = None

    def _build(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.window = ctk.CTk()
        self.window.title("Emotion Music Recommender")
        self.window.geometry(f"{config.UI.WIDTH}x{config.UI.HEIGHT}")
        self.window.minsize(900, 600)
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        self.home = HomeView(self.window)
        self.home.pack(fill="both", expand=True)
        # Auto-start camera after UI settles
        self.window.after(400, self.home.start_camera)

    def _on_close(self) -> None:
        if self.home is not None:
            self.home.stop_camera()
            self.home.shutdown()
        self.window.destroy()

    def run(self) -> None:
        self._build()
        self.window.mainloop()
