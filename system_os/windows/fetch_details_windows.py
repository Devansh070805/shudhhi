import subprocess
import re
import json

def get_disk_info_windows(disk_identifier):

    try:
        ps_cmd = (
            f"Get-CimInstance Win32_DiskDrive | "
            f"Where-Object {{ $_.DeviceID -eq '{disk_identifier}' }} | "
            f"Select-Object * | "
            f"ConvertTo-Json -Compress"
        )
        
        result = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, check=True)
        
        # If no disk is found, the output will be empty.
        if not result.stdout.strip():
            print(f"Error: Disk '{disk_identifier}' not found.")
            return None

        data = json.loads(result.stdout)
        
        details = {}
        
        # Model
        details['model'] = data.get("Model", "N/A")
        
        # Capacity
        size_bytes = int(data.get("Size", 0))
        details["capacity"] = f"{size_bytes / (10**9):.2f} GB" if size_bytes > 0 else "0.00 GB"

        # Serial Number
        details["serial_number"] = data.get("SerialNumber", "N/A").strip()

        # Vendor and Product ID (extracted from PNPDeviceID)
        pnp_device_id = data.get("PNPDeviceID", "")
        vendor_match = re.search(r"VEN_([^&]+)", pnp_device_id)
        product_match = re.search(r"PROD_([^&]+)", pnp_device_id)
        
        details["vendor_id"] = vendor_match.group(1) if vendor_match else "N/A"
        details["product_id"] = product_match.group(1) if product_match else "N/A"
        
        # Manufacturer
        details["manufacturer"] = data.get("Manufacturer", "N/A")
        
        # Bus
        details["bus"] = data.get("InterfaceType", "N/A")

        # --- Hardcoded fields to match the darwin script's output ---
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
