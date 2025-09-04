# Generates wipe reports for Android

import datetime

def generate_wipe_report(disk_info, algorithm, status):
    """
    Generates a report after wiping a disk.
    Returns a dictionary with the report details.
    """
    report = {
        "disk_info": disk_info,
        "algorithm": algorithm,
        "status": status,
        "timestamp": datetime.datetime.now().isoformat()
    }
    return report
