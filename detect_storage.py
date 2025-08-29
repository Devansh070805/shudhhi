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

print(disks)

name_to_id = {} # dictionary to map the selected name to its disk_id

# function to get the manufacturers name to make it easier for the user
def replace_with_name(disk_id):
     name =  subprocess.getoutput(f"diskutil info {disk_id} | grep 'Device / Media Name'").split(":")[-1].strip()
     name_to_id[name] = "/dev/" + disk_id
     return name

# a dictionary to story data of format -> disk_name: storage
for line in disks.split("\n"):
    # for Darwin
    if '*' in line:
        if disk_name == '':
            continue
        sp = line.split()
        size = sp[2][1:] + " " +  sp[3]
        disk_info[replace_with_name(disk_name)] = size
        disk_name = ''
        
    if line.startswith("/dev/") and line.endswith("(external, physical):"): # extracting only the physical devices and not their partitions
        disk_name = line.split()[0][5:] # this extracts the name of the disk 
        '''
        on analyzing the outptu format we can see that the storage capacity
        of physical devices is marked with '*', so we can write a simple logic for that
        coudl also arguably use the 'identifier' name is above '*' logic to simply fetch the name check once later.
        NOTE -> FOR KNOW I AM ONLY ALLOWING EXTERNAL DRIVES TO SHOW UP FOR WIPING TO PREVENT ANY MISTAKE
        WRITE LOGIC TO HANDLE NO EXTERNAL DEVICES CONNECTED
        '''
    

print(disk_info)
print(name_to_id)

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
combo.current(0)
print("ddd", combo.get())

button = tk.Button(root, text="Wipe Now", command=on_button_click)
button.grid(row=2, column=0, pady=20)



root.mainloop()