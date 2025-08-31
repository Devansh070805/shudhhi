import json
import datetime
import os
import uuid
import hashlib
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.graphics.barcode import code128

class ReportGenerator:

    def __init__(self, config_path="config.json"):
        """Loads the static configuration from the specified JSON file."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            full_config_path = os.path.join(script_dir, config_path)
            
            with open(full_config_path, 'r') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"Warning: '{config_path}' not found or invalid in the script's directory. Using empty config.")
            self.config = {}


    def _generate_hash(self, data_dict):
        """
        Creates a SHA-256 hash of the report data for integrity verification.
        """
        # Create a consistent, sorted JSON string of the data to ensure the hash is repeatable.
        canonical_string = json.dumps(data_dict, sort_keys=True)
        return hashlib.sha256(canonical_string.encode('utf-8')).hexdigest()
    
    
    def _draw_header(self, c, width, height, report_data):
        """Draws the top section of the report, including titles and status."""
        
        # LOGO 1:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        logo_left_path = os.path.join(BASE_DIR, "..", "assets", "logo.png")
        print("Logo exists?", os.path.exists(logo_left_path))
        if os.path.exists(logo_left_path):
            c.drawImage(logo_left_path, 0.6 * inch, height - 1.3 * inch, width=1.0*inch, height=1.0*inch, preserveAspectRatio=True, mask='auto')
        else:
            c.rect(0.6 * inch, height - 1.3 * inch, 1.0*inch, 1.0*inch, stroke=1, fill=0)
            c.drawCentredString(1.1 * inch, height - 0.8 * inch, "Logo 1")

        # LOGO 2:
        if report_data.get('dynamic_data').get('status') == 'Success':
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            logo_right_path = os.path.join(BASE_DIR, "..", "assets", "success.png")
            print("Logo exists?", os.path.exists(logo_right_path))
        else:
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            logo_right_path = os.path.join(BASE_DIR, "..", "assets", "failed.png") 
            print("Logo exists?", os.path.exists(logo_right_path))

        if os.path.exists(logo_right_path):
            # Position this logo on the far right side
            c.drawImage(logo_right_path, width - 1.6 * inch, height - 1.3 * inch, width=1.0*inch, height=1.0*inch, preserveAspectRatio=True, mask='auto')
        else:
            c.rect(width - 1.6 * inch, height - 1.3 * inch, 1.0*inch, 1.0*inch, stroke=1, fill=0)
            c.drawCentredString(width - 1.1 * inch, height - 0.8 * inch, "Logo 2")

        c.setFillColor(colors.black)

        # --- MODEL AND SERIAL (Top-Center) ---
        c.setFont("Helvetica-Bold", 14)
        model = report_data.get('dynamic_data', {}).get("model", "N/A")
        serial = report_data.get('dynamic_data', {}).get("serial_number", "N/A")
        c.drawCentredString(width / 2.0, height - 0.5 * inch, f"Model: {model}")
        c.drawCentredString(width / 2.0, height - 0.7 * inch, f"S/N: {serial}")

        # --- MAIN TITLE (Center) ---
        # Draw the main page heading
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width / 2.0, height - 1.15 * inch, self.config.get("page_heading", "Disk Erasure Report"))  # moved slightly up

        # Draw "Erasure Status" with extra spacing above and below
        c.setFont("Helvetica", 12)
        y_status = height - 1.6 * inch  # y-position for status text
        c.drawCentredString(width / 2.0, y_status + 0.1 * inch, "")  # extra spacing above
        #c.drawCentredString(width / 2.0, y_status, "Erasure Status")
        c.drawCentredString(width / 2.0, y_status - 0.1 * inch, "")  # extra spacing below


        # --- BARCODE (Below Title) ---
        report_id = report_data.get("report_id", "")
        if report_id:
            barcode = code128.Code128(report_id, barHeight=0.4*inch, barWidth=1)
            barcode_width = barcode.width
            # Center the barcode on the page
            barcode.drawOn(c, (width - barcode_width) / 2.0, height - 1.8 * inch)

    def _draw_section_table(self, c, y_start, title, left_data, right_data):
        """Draws a two-column section with perfectly aligned text using a Table."""
        c.setFont("Helvetica-Bold", 11)
        c.setFillColorRGB(0.2, 0.2, 0.5) # Dark blue for title
        c.drawString(0.7 * inch, y_start, title)
        c.line(0.7 * inch, y_start - 0.05 * inch, 7.8 * inch, y_start - 0.05 * inch)
        c.setFillColor(colors.black)

        table_data = []
        max_rows = max(len(left_data), len(right_data))
        for i in range(max_rows):
            row = []
            if i < len(left_data):
                row.extend([f"{left_data[i][0]}:", left_data[i][1]])
            else:
                row.extend(["", ""])
            
            if i < len(right_data):
                row.extend([f"{right_data[i][0]}:", right_data[i][1]])
            else:
                row.extend(["", ""])
            table_data.append(row)

        table = Table(table_data, colWidths=[1.2 * inch, 2.5 * inch, 1.2 * inch, 2.5 * inch])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue), 
            ('TEXTCOLOR', (2, 0), (2, -1), colors.darkblue), 
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (1, 0), (1, -1), 10),
            ('RIGHTPADDING', (3, 0), (3, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        table_height = table.wrapOn(c, 0, 0)[1]
        table.drawOn(c, 0.9 * inch, y_start - 0.15 * inch - table_height)
        
        return y_start - table_height - 0.3 * inch

    def generate_pdf(self, dynamic_details):

        report_data = {
            "report_id": str(uuid.uuid4()),
            "config_data": self.config,
            "dynamic_data": dynamic_details
        }

        global signature
        signature = self._generate_hash(report_data)

        output_filename=f"Shudhhi-Report-{signature}.pdf"

        c = canvas.Canvas(output_filename, pagesize=letter)
        width, height = letter
        
        self._draw_header(c, width, height, report_data)

        y_pos = height - 2.2 * inch

        # --- Organization Section (Data from config.json) ---
        org = self.config.get("organization_performing_the_disc_erasure", {})
        org_left = [("Business Name", org.get("Business Name")), ("Business Address", org.get("Business Address"))]
        org_right = [("Contact Name", org.get("Contact Name")), ("Contact Phone", org.get("Contact Phone"))]
        y_pos = self._draw_section_table(c, y_pos, "Organisation Performing The Disk Erasure", org_left, org_right)

        y_pos -= 0.4 * inch

        # --- Customer Details Section (Data from dynamic_details) ---
        #cust = dynamic_details.get("Customer Details", {})
        cust_left = [("Name", dynamic_details.get("customer_name")), ("Address", dynamic_details.get("customer_address"))]
        cust_right = [("Contact Name", dynamic_details.get("customer_contact_name")), ("Contact Phone", dynamic_details.get("customer_contact_phone"))]
        y_pos = self._draw_section_table(c, y_pos, "Customer Details", cust_left, cust_right)

        y_pos -= 0.4 * inch

        # --- Disk Information Section (Data from dynamic_details) ---
        #disk = dynamic_details.get("Disk Information", {})
        disk_left = [("Make/Model", dynamic_details.get("model")), ("Disk Capacity", dynamic_details.get("capacity"))]
        disk_right = [("Serial No.", dynamic_details.get("serial_number")), ("Bus", dynamic_details.get("bus"))]
        y_pos = self._draw_section_table(c, y_pos, "Disk Information", disk_left, disk_right)

        y_pos -= 0.4 * inch

        # --- Disk Erasure Details Section (Data from dynamic_details) ---
        #erase = dynamic_details.get("Disk Erasure Details", {})
        erase_left = [("Start time", dynamic_details.get("start_time")), ("Duration", dynamic_details.get("duration")), ("Method", dynamic_details.get("method")),("Verify Pass:", 'Verify All'),("HPA/DCO Size:", dynamic_details.get("hpa_dco_size"))]
        erase_right = [("End time", dynamic_details.get("end_time")), ("Status", dynamic_details.get("status")),("Final Pass:", dynamic_details.get("final_pass")),("HPA/DCO:", dynamic_details.get("hpa_dco"))]
        y_pos = self._draw_section_table(c, y_pos, "Disk Erasure Details", erase_left, erase_right)

        y_pos -= 0.4 * inch

        # --- Technician Section (Data from config.json) ---
        tech = self.config.get("technician_id", {})
        tech_left = [("Name/ID", tech.get("Name/ID"))]
        tech_right = [("Signature", "")] # Signature is always blank
        y_pos = self._draw_section_table(c, y_pos, "Technician/Operator ID", tech_left, tech_right)
        
        # Draw a line for the signature
        c.line(5.8 * inch, y_pos + 0.15*inch, 7.6 * inch, y_pos + 0.15*inch)

        # --- Digital Signature Section ---
        y_pos -= 0.5 * inch
        c.setFont("Helvetica-Bold", 10)
        c.drawString(0.7*inch, y_pos, "Digital Signature (SHA-256)")
        c.setFont("Courier", 7)
        c.drawString(0.7*inch, y_pos - 0.15*inch, signature)
        
        # --- Footer ---
        footer_text = f"Disk Erasure by {self.config.get('software_name', 'Shudhhi')} version {self.config.get('software_version', '1.0.0')}"
        c.setFont("Helvetica", 9)
        c.drawCentredString(width / 2.0, 0.5 * inch, footer_text)

        c.save()
        print(f"Successfully generated PDF report: {output_filename}")




