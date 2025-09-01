import subprocess
import re
import json

def get_disk_info_linux(disk_identifier):
    try:
        cmd = ["lsblk", "-J", "-o", "NAME,SIZE,MODEL,SERIAL,VENDOR,TRAN", disk_identifier]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if not result.stdout.strip():
            print(f"Error: Disk '{disk_identifier}' not found or no info available.")
            return None

        data = json.loads(result.stdout)["blockdevices"][0]
        
        details = {}
        
        # Model
        details['model'] = data.get("model", "N/A")
        
        # Capacity
        details["capacity"] = data.get("size", "N/A")

        # Serial Number
        details["serial_number"] = data.get("serial", "N/A")

        # Vendor ID (Vendor string is the closest equivalent)
        details["vendor_id"] = data.get("vendor", "N/A")
        
        # Product ID (Not typically provided by lsblk, so we default to N/A)
        details["product_id"] = "N/A"
        
        # Manufacturer (Vendor string is the closest equivalent)
        details["manufacturer"] = data.get("vendor", "N/A")
        
        # Bus (Transport type, e.g., "usb", "sata", "nvme")
        details["bus"] = data.get("tran", "N/A").upper()

        # --- Hardcoded fields to match the other scripts' output ---
        details['method'] = 'Single pass zero (0)'
        details['final_pass'] = 'Zeroes'
        details['rounds_requested'] = '1'
        details['rounds_completed'] = '1'
        details['hpa_dco'] = 'No hidden sectors'
        details['hpa_dco_size'] = 'No hidden sectors'

        details['customer_name'] = 'Devu Enterprises'
        details['customer_address'] = 'Lucknow'
        details['customer_contact_name'] = 'Devuchan'
        details['customer_contact_phone'] = '+91 XXXXXXXXXX'
        
        return details

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

