# this script is used to detect the mouted drives and storages

'''
since this is a cross-platform software and we need to access areas restricted by HPA/DCO, i am writing os specific scripts 
to get the information we need

'''
import platform
import json
import re
import tkinter as tk
from tkinter import ttk
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

root = tk.Tk()
root.title("Select your Drive: ")
root.geometry("400x200")

oss = f'Detected System: {os_name}'
lbl = tk.Label(root, text=oss)
lbl.grid(row=0, column=0, padx=10, pady=10)

combo = ttk.Combobox(root, values=display_options, state="readonly")
combo.grid(row=1, column=0, padx=10, pady=10)

combo.bind("<<ComboboxSelected>>", on_select)
combo.current(0)

root.mainloop()


