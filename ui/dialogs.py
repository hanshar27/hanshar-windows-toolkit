import customtkinter as ctk


def show_error_dialog(parent, title: str, message: str):
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("420x150")
    dialog.transient(parent)
    dialog.grab_set()
    label = ctk.CTkLabel(dialog, text=message, wraplength=360)
    label.pack(padx=20, pady=(20, 10))
    button = ctk.CTkButton(
        dialog, text="OK", command=dialog.destroy, corner_radius=12
    )
    button.pack(pady=10)


def show_info_dialog(parent, title: str, message: str):
    show_error_dialog(parent, title, message)
