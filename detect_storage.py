# this script is used to detect the mouted drives and storages

'''
since this is a cross-platform software and we need to access areas restricted by HPA/DCO, i am writing os specific scripts 
to get the information we need

'''
import platform
import json
import re
import tkinter as tk
from tkinter import ttk, messagebox
from linux_disks import get_disks_linux
from windows_disks import get_disks_windows
from macos_disks import get_disks_darwin
from android_disks import get_disks_android


os_name = platform.system()
print(f'Detected System: {os_name}')

if os_name == 'Linux':
    disks = get_disks_linux()
elif os_name == 'Windows':
    disks = get_disks_windows()
elif os_name == 'Darwin':
    disks = get_disks_darwin()
else:
    disks = get_disks_android()

disk_info = {} 
disk_name = ''
counter = 0

# a dictionary to story data of format -> disk_name: storage
for line in disks.split("\n"):
    # for Darwin
    if '*' in line:
        sp = line.split()
        size = sp[2][1:] + " " +  sp[3]
        disk_info[disk_name] = size
        
    if line.startswith("/dev/") and line.endswith("physical):"): # extracting only the physical devices and not their partitions
        disk_name = line.split()[0][5:] # this extracts the name of the disk 
        '''
        on analyzing the outptu format we can see that the storage capacity
        of physical devices is marked with '*', so we can write a simple logic for that
        coudl also arguably use the 'identifier' name is above '*' logic to simply fetch the name check once later.

        '''
    

print(disk_info)

display_options = [f"{k} - {v}" for k, v in disk_info.items()]

def on_select(event):
    selected_display = combo.get()
    selected_key = selected_display.split(" - ")[0]
    selected_info = disk_info[selected_key]
    print(f"You selected: {selected_key} -> {selected_info}")

def show_warning(selected_disk):
    """Custom warning dialog with Continue / Cancel buttons"""
    warning = tk.Toplevel(root)
    warning.title("⚠️ WARNING")
    warning.geometry("400x200")
    warning.grab_set()  

    msg = (
        f"You are about to permanently ERASE all data on:\n\n"
        f"{selected_disk}\n\n"
        f"This action cannot be undone!"
    )
    tk.Label(warning, text=msg, wraplength=350, justify="left", fg="red").pack(pady=10)

    # Buttons
    btn_frame = tk.Frame(warning)
    btn_frame.pack(pady=20)

    def on_continue():
        print("User chose CONTINUE — wiping disk...")
        warning.destroy() 

    def on_cancel():
        print("User chose CANCEL — returning to disk selection")
        warning.destroy()  

    tk.Button(btn_frame, text="Cancel", command=on_cancel).grid(row=0, column=1, padx=10)
    tk.Button(btn_frame, text="Continue", command=on_continue).grid(row=0, column=0, padx=10)

def on_button_click():
    selected_disk = combo.get()
    if selected_disk:
        show_warning(selected_disk)
    else:
        messagebox.showwarning("No Selection", "Please select a disk first!")

root = tk.Tk()
root.title("Select your Drive: ")
root.geometry("400x200")

oss = f"Detected System: {os_name}"
lbl = tk.Label(root, text=oss)
lbl.grid(row=0, column=0, padx=10, pady=10)

combo = ttk.Combobox(root, values=display_options, state="readonly")
combo.grid(row=1, column=0, padx=10, pady=10)

combo.bind("<<ComboboxSelected>>", on_select)
combo.current(0)

button = tk.Button(root, text="Wipe Now", command=on_button_click)
button.grid(row=2, column=0, pady=20)

root.mainloop()