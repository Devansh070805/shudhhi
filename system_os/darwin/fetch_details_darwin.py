import subprocess
import re
import json

def get_disk_info_darwin(disk_identifier):

    disk_identifier = disk_identifier[5:]
    print(disk_identifier)
    try:
        cmd = ["system_profiler", "SPUSBDataType"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout

        # Step 1: Split the output into chunks based on one or more blank lines.
        # This is more robust than a simple split on '\n\n'.
        device_chunks = re.split(r'\n\s*\n', output)
        
        target_chunk = None
        # Step 2: Find the specific chunk for our target disk.
        for chunk in device_chunks:
            if f"BSD Name: {disk_identifier}" in chunk:
                target_chunk = chunk
                print(target_chunk)
                break # Found it, no need to search further.

        if target_chunk:
            # Step 3: Perform regex matching on the found chunk only.
            details = {}
            model_name = re.search(r"Media:\s+([A-Za-z0-9\s]+):", target_chunk)
            if model_name:
                details['model'] = model_name.group(1).strip() 
            else:
                details['model'] = 'Not Found' 

            # Regex for "Capacity: ... (15,376,318,464 bytes)"
            capacity_match = re.search(r"Capacity:\s*([\d\.]+\s*\w+)", target_chunk)
            if capacity_match:
                size_bytes_str = capacity_match.group(1).replace(',', '')
                details["capacity"] = size_bytes_str
            else:
                details["capacity"] = 0

            # Regex for "Serial Number: ..."
            serial_match = re.search(r"Serial Number:\s*(.+)", target_chunk)
            details["serial_number"] = serial_match.group(1).strip() if serial_match else "N/A"
            
            # Regex for "Product ID: ..."
            product_id_match = re.search(r"Product ID:\s*(.+)", target_chunk)
            details["product_id"] = product_id_match.group(1).strip() if product_id_match else "N/A"

            # Regex for "Vendor ID: ..."
            vendor_id_match = re.search(r"Vendor ID:\s*(.+)", target_chunk)
            details["vendor_id"] = vendor_id_match.group(1).strip().split()[0] if vendor_id_match else "N/A"

            # Regex for "Manufacturer: ..."
            manufacturer_match = re.search(r"Manufacturer:\s*(.+)", target_chunk)
            details["manufacturer"] = manufacturer_match.group(1).strip() if manufacturer_match else "N/A"

            # cause BUS
            details["bus"] = 'BUS'

            # i am just writing these extras hardcoded here. these may or may not go here.
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
        else:
            print(f"Error: Disk '{disk_identifier}' not found in system_profiler output.")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# --- Example of how to run it ---
if __name__ == "__main__":
    # Replace 'disk10' with a real external disk identifier from your system.
    target_disk_id = "disk10" 
    
    disk_details = get_disk_info_darwin(target_disk_id)
    
    if disk_details:
        # Pretty print the JSON output
        print(json.dumps(disk_details, indent=4))

