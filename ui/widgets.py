import customtkinter as ctk


def make_label(master, text: str, size: int = 14):

    return ctk.CTkLabel(master, text=text, font=("Segoe UI", size))
