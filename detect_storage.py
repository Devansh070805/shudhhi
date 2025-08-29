# this script is used to detect the mouted drives and storages

'''
since this is a cross-platform software and we need to access areas restricted by HPA/DCO, i am writing os specific scripts 
to get the information we need

'''
import platform
import json
import re
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from linux_disks import get_disks_linux
from windows_disks import get_disks_windows
from macos_disks import get_disks_darwin
from android_disks import get_disks_android
from wipe_disk import do_wipe


os_name = platform.system()
print(f'Detected System: {os_name}')


if os_name == 'Darwin':
    from macos_disks import get_external_disks_darwin
    disk_info, name_to_id = get_external_disks_darwin()
else:
    if os_name == 'Windows':
        disk_info = get_disks_windows()
        name_to_id = {k: k for k in disk_info.keys()}  # Use disk name as ID for Windows
    else:
        disks = None
        if os_name == 'Linux':
            disks = get_disks_linux()
        else:
            disks = get_disks_android()

        disk_info = {}
        disk_name = ''
        name_to_id = {}
        print(disks)
        # ...existing code for non-macOS parsing (if any, e.g. Linux/Android)...

display_options = [f"{k} - {v}" for k, v in disk_info.items()]

def on_select(event):
    selected_display = combo.get()
    selected_key = selected_display.split(" - ")[0]
    selected_info = disk_info[selected_key]
    print(f"You selected: {selected_key} - {selected_info}")


def show_warning(selected_display):
    warning = tk.Toplevel(root)
    warning.title("WARNING!!!")
    warning.geometry("400x200")
    warning.grab_set()  
    warning.attributes("-topmost", True)

    msg = (
        f"You are about to permanently ERASE all data on:\n\n"
        f"{selected_display}\n\n"
        f"This action cannot be undone!"
    )
    tk.Label(warning, text=msg, wraplength=350, justify="left", fg="red").pack(pady=10)

    selected_key = selected_display.split(" - ")[0]

    btn_frame = tk.Frame(warning)
    btn_frame.pack(pady=20)

    def on_continue():
        disk_id = name_to_id[selected_key]  
        print(f"User chose CONTINUE — wiping {disk_id}...")
        warning.destroy()
        # THIS IS THE FUNCTION CALL TO WIPE THE DATA
        do_wipe.do_wipe_darwin(disk_id)

    def on_cancel():
        print("User chose CANCEL — returning to disk selection")
        warning.destroy()

    tk.Button(btn_frame, text="Cancel", command=on_cancel).grid(row=0, column=1, padx=10)
    tk.Button(btn_frame, text="Yes, Erase", command=on_continue).grid(row=0, column=0, padx=10)


def on_button_click():
    selected_disk = combo.get()
    if selected_disk:
        show_warning(selected_disk)
    else:
        messagebox.showwarning("No Selection", "Please select a disk first!")

root = tk.Tk()
root.title("Select your Drive: ")
root.geometry("400x200")
root.attributes("-topmost", True)

oss = f"Detected System: {os_name}"
lbl = tk.Label(root, text=oss)
lbl.grid(row=0, column=0, padx=10, pady=10)

combo = ttk.Combobox(root, values=display_options, state="readonly")
combo.grid(row=1, column=0, padx=10, pady=10)

combo.bind("<<ComboboxSelected>>", on_select)
if display_options:
    combo.current(0)
    print("ddd", combo.get())

button = tk.Button(root, text="Wipe Now", command=on_button_click)
button.grid(row=2, column=0, pady=20)



root.mainloop()