#!/usr/bin/env python3
"""
Cisco Catalyst Center License Report Generator
Authenticates to Catalyst Center, queries license device summary API with pagination,
filters unregistered devices, and generates a Cisco-branded PDF report.
"""

import sys
import getpass
import datetime

# Dependency import guards
try:
    import requests
except ImportError:
    print("Error: Missing required package 'requests'")
    print("Install with: pip install requests")
    sys.exit(1)

try:
    from fpdf import FPDF
except ImportError:
    print("Error: Missing required package 'fpdf2'")
    print("Install with: pip install fpdf2")
    sys.exit(1)

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

# Cisco blue color
CISCO_BLUE = (4, 159, 217)


class CiscoPDF(FPDF):
    """PDF subclass with Cisco branding header and footer."""
    
    def header(self):
        """Add Cisco-branded header to each page with blue background."""
        # Draw blue background rectangle (full width, 30mm height)
        self.set_fill_color(*CISCO_BLUE)
        self.rect(x=0, y=0, w=self.w, h=30, fill=True)
        
        # Draw "CISCO" wordmark in white bold text
        self.set_font("Helvetica", "B", 24)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 8)
        self.cell(0, 14, "CISCO", ln=False)
        
        # Add title below wordmark
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 18)
        self.cell(0, 8, "Unregistered Device Licence Report", ln=True)
        
        # Add spacing after header
        self.ln(5)
    
    def footer(self):
        """Add footer with page number and generation info."""
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f"Page {self.page_no()}", align="C", ln=True)
        self.cell(0, 5, "Generated from Cisco Catalyst Center", align="C")


def get_auth_token(base_url, username, password):
    """
    Authenticate to Catalyst Center and retrieve auth token.
    
    Args:
        base_url: Base URL of Catalyst Center (e.g., https://192.168.1.1)
        username: Username for authentication
        password: Password for authentication
    
    Returns:
        Authentication token string
    
    Raises:
        SystemExit: On authentication failure
    """
    try:
        auth_url = f"{base_url}/dna/system/api/v1/auth/token"
        response = requests.post(
            auth_url,
            auth=(username, password),
            verify=False,
            timeout=10
        )
        response.raise_for_status()
        token = response.json().get("Token")
        if not token:
            print("Error: No token received from authentication endpoint.")
            sys.exit(1)
        print("✓ Authentication successful")
        return token
    except requests.exceptions.RequestException as e:
        print(f"Error: Authentication failed - {e}")
        sys.exit(1)


def get_all_devices(base_url, token):
    """
    Retrieve all devices from license device summary API with pagination.
    
    Args:
        base_url: Base URL of Catalyst Center
        token: Authentication token
    
    Returns:
        List of device dictionaries
    
    Raises:
        SystemExit: On API failure
    """
    try:
        devices = []
        page_number = 1
        limit = 500
        total = None
        
        while True:
            api_url = f"{base_url}/dna/intent/api/v1/licenses/device/summary"
            params = {
                "page_number": page_number,
                "order": "asc",
                "sort_by": "device_name",
                "limit": limit
            }
            headers = {
                "X-Auth-Token": token,
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                api_url,
                headers=headers,
                params=params,
                verify=False,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract total on first request
            if total is None:
                total = data.get("total", 0)
                print(f"✓ Found {total} total devices")
            
            # Extract devices from response
            page_devices = data.get("response", [])
            if not page_devices:
                break
            
            devices.extend(page_devices)
            print(f"  Retrieved {len(devices)}/{total} devices")
            
            # Check if we've retrieved all devices
            if len(devices) >= total:
                break
            
            page_number += 1
        
        print(f"✓ Retrieved all {len(devices)} devices")
        return devices
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to retrieve devices - {e}")
        sys.exit(1)


def filter_unregistered(devices):
    """
    Filter devices with unregistered status (smart_account_name is None, empty, or "NA").
    
    Args:
        devices: List of device dictionaries
    
    Returns:
        List of unregistered device dictionaries
    """
    unregistered = []
    for device in devices:
        smart_account = device.get("smart_account_name")
        if smart_account is None or smart_account == "" or smart_account == "NA":
            unregistered.append(device)
    
    print(f"✓ Filtered {len(unregistered)} unregistered devices")
    return unregistered


def generate_pdf(devices, filename):
    """
    Generate Cisco-branded PDF report with device table (3 columns).
    
    Args:
        devices: List of device dictionaries to include in report
        filename: Output filename for PDF
    
    Raises:
        SystemExit: On PDF generation failure
    """
    try:
        pdf = CiscoPDF(orientation="L", unit="mm", format="A4")
        pdf.add_page()
        
        # Table header with Cisco blue background and white text
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(*CISCO_BLUE)
        
        # Column widths for landscape A4 (~277mm usable): 40%, 30%, 30%
        col_widths = [111, 83, 83]
        headers = ["Device Name", "IP Address", "Network License"]
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, border=1, align="C", fill=True, new_x="RIGHT", new_y="TOP")
        pdf.ln()
        
        # Table rows with alternating white/light-gray fill
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        
        row_color = False
        for device in devices:
            device_name = device.get("device_name", "N/A")[:30]
            ip_address = device.get("ip_address", "N/A")
            network_license = device.get("network_license", "N/A")
            
            if row_color:
                pdf.set_fill_color(242, 242, 242)
            else:
                pdf.set_fill_color(255, 255, 255)
            
            pdf.cell(col_widths[0], 8, device_name, border=1, align="L", fill=True, new_x="RIGHT", new_y="TOP")
            pdf.cell(col_widths[1], 8, ip_address, border=1, align="L", fill=True, new_x="RIGHT", new_y="TOP")
            pdf.cell(col_widths[2], 8, network_license, border=1, align="L", fill=True, new_x="RIGHT", new_y="TOP")
            pdf.ln()
            
            row_color = not row_color
        
        pdf.output(filename)
        print(f"✓ PDF report generated: {filename}")
    except Exception as e:
        print(f"Error: Failed to generate PDF - {e}")
        sys.exit(1)


def main():
    """Main execution flow with interactive prompts."""
    print("\n" + "="*60)
    print("Cisco Catalyst Center - License Report Generator")
    print("="*60 + "\n")
    
    # Interactive prompts
    hostname = input("Catalyst Center hostname or IP: ").strip()
    if not hostname:
        print("Error: Hostname or IP is required.")
        sys.exit(1)
    
    base_url = f"https://{hostname}"
    
    username = input("Enter username: ").strip()
    if not username:
        print("Error: Username is required.")
        sys.exit(1)
    
    password = getpass.getpass("Enter password: ")
    if not password:
        print("Error: Password is required.")
        sys.exit(1)
    
    # Authentication
    print("\nAuthenticating...")
    token = get_auth_token(base_url, username, password)
    
    # Retrieve devices
    print("\nRetrieving devices...")
    devices = get_all_devices(base_url, token)
    
    # Filter unregistered
    print("\nFiltering unregistered devices...")
    unregistered = filter_unregistered(devices)
    
    if not unregistered:
        print("No unregistered devices found.")
        sys.exit(0)
    
    # Generate PDF
    print("\nGenerating PDF report...")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"unregistered_devices_{timestamp}.pdf"
    generate_pdf(unregistered, filename)
    
    print("\n" + "="*60)
    print(f"Report complete: {filename}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
