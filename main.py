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
import threading
from tkinter import ttk, messagebox
from system_os.linux.linux_disks import get_disks_linux
from system_os.windows.windows_disks import get_disks_windows
from system_os.darwin.darwin_disks import get_disks_darwin
from system_os.android.android_disks import get_disks_android
from wipe_disk import do_wipe


os_name = platform.system() # this is used to store the name of the operating system
print(f'Detected System: {os_name}')

if os_name == 'Linux':
    disk_info, name_to_id = get_disks_linux()
elif os_name == 'Windows':
    disk_info, name_to_id = get_disks_windows()
elif os_name == 'Darwin':
    disk_info, name_to_id  = get_disks_darwin()
else:
    disk_info, name_to_id = get_disks_android()

    # need to handle the else case

# REQUIREMENTS:
# disk_info -> {disk_name: disk_size}
# name_to_id -> {disk_name: disk_id}

# display_options = ["Select Drive to Proceed:"]
display_options = [f"{k} - {v}" for k, v in disk_info.items()]
# if not display_options:
#     display_options = ["No external drives detected"]

animation_id = None
root = tk.Tk() 

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
        start_wipe_ui(disk_id, selected_display)

    def on_cancel():
        print("User chose CANCEL — returning to disk selection")
        warning.destroy()

    tk.Button(btn_frame, text="Cancel", command=on_cancel).grid(row=0, column=1, padx=10)
    tk.Button(btn_frame, text="Yes, Erase", command=on_continue).grid(row=0, column=0, padx=10)


def animate_spinner(spinner_label, step=0):
    global animation_id
    spinner_chars = ['|', '/', '-', '\\']
    spinner_label.config(text=spinner_chars[step % len(spinner_chars)])
    animation_id = root.after(100, animate_spinner, spinner_label, step + 1)

def start_wipe_ui(disk_id, display_name):
    progress_window = tk.Toplevel(root)
    progress_window.title("Wipe in Progress")
    progress_window.geometry("500x300")
    progress_window.grab_set()
    progress_window.attributes("-topmost", True)
    
    status_frame = tk.Frame(progress_window)
    status_frame.pack(pady=10, padx=10, fill='x')

    spinner_label = ttk.Label(status_frame, text="", font=("Courier", 16))
    spinner_label.pack(side='left', padx=(0, 10))

    status_label = ttk.Label(status_frame, text=f"Preparing to wipe {display_name}...")
    status_label.pack(side='left')
    
    log_box = tk.Text(progress_window, height=8, width=60, state='disabled', bg='#f0f0f0', disabledforeground='black') # added black text for readability
    log_box.pack(pady=10, padx=10, fill="both", expand=True)
    
    wipe_thread = threading.Thread(
        target=run_wipe_in_thread,
        args=(disk_id, status_label, spinner_label, log_box)
    )
    wipe_thread.start()


def run_wipe_in_thread(disk_id, status_label, spinner_label, log_box):
    global animation_id

    def append_log(line):
        log_box.config(state='normal')
        log_box.insert(tk.END, line + "\n")
        log_box.see(tk.END)
        log_box.config(state='disabled')

    def state_callback(state, line=None):
        if state == "wiping":
            root.after(0, animate_spinner, spinner_label)
            root.after(0, lambda: status_label.config(text=f"Wiping {disk_id}..."))
        elif state == "logging":
            root.after(0, append_log, line)
        elif state == "finalizing":
            root.after(0, lambda: status_label.config(text="Almost done, finalizing... This may take a while."))

    success, message = (False, "")
    try:
        # THIS IS THE FUNCTION CALL TO WIPE THE DATA
        if os_name == 'Linux':
            success, message = do_wipe.do_wipe_linux(disk_id, state_callback)
        elif os_name == 'Windows':
            success, message = do_wipe.do_wipe_windows(disk_id, state_callback)
        elif os_name == 'Darwin':
            success, message = do_wipe.do_wipe_darwin(disk_id, state_callback)
        else:
            success, message = do_wipe.do_wipe_android(disk_id, state_callback)
        
    finally:
        if animation_id:
            root.after(0, root.after_cancel, animation_id)
            animation_id = None

    if success:
        root.after(0, lambda: spinner_label.config(text="✅"))
        root.after(0, lambda: status_label.config(text=message))
        # Auto-close the window after 5 seconds on success
        # maybe add an option to close the window manually lets see
        root.after(5000, status_label.master.master.destroy)
    else:
        root.after(0, lambda: spinner_label.config(text="❌"))
        root.after(0, lambda: status_label.config(text="Wipe Failed!"))
        messagebox.showerror("Wipe Failed", message, parent=status_label.master.master)


def on_button_click():
    selected_disk = combo.get()
    if selected_disk:
        show_warning(selected_disk)
    else:
        messagebox.showwarning("No Selection", "Please select a disk first!")

root.title("Select your Drive: ")
root.geometry("400x200")
root.attributes("-topmost", True)

oss = f"Detected System: {os_name}"
lbl = tk.Label(root, text=oss)
lbl.grid(row=0, column=0, padx=10, pady=10)

button = tk.Button(root, text="Wipe Now", command=on_button_click)
button.grid(row=2, column=0, pady=20)

combo = ttk.Combobox(root, values=display_options, state="readonly")
combo.grid(row=1, column=0, padx=10, pady=10)

combo.bind("<<ComboboxSelected>>", on_select)

if display_options:  
    combo.current(0)  
else:
    combo.set("No external disks detected")
    button.config(state="disabled")

root.mainloop()