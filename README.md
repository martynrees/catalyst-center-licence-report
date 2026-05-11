# Catalyst Center Licence Report Generator

A standalone Python script that authenticates to Cisco Catalyst Center, queries the licence device summary API, filters devices not registered to a Smart Account, and generates a Cisco-branded PDF report. Built for network engineers and IT administrators who need to identify unregistered devices for licence compliance.

## Features

- Interactive credential prompts with hidden password input (no hardcoded secrets)
- Automatic pagination for large device inventories (500 devices per page)
- Filters devices where `smart_account_name` is `"NA"`, `None`, or empty
- Cisco-branded PDF output with:
  - Blue header bar with "CISCO" wordmark
  - Table with columns: Device Name, IP Address, Network License
  - Alternating row colours for readability
  - Page numbering in footer

## Prerequisites

- Python 3.7 or later
- Access to a Cisco Catalyst Center instance
- User credentials with API access
- Required Python packages: `requests`, `fpdf2`

## Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/martynrees/catalyst-center-licence-report.git
cd catalyst-center-licence-report
pip install requests fpdf2
```

## Usage

Run the script from your terminal:

```bash
python licence_report.py
```

You'll be prompted for three pieces of information:

1. **Catalyst Center hostname or IP address** (e.g. `10.1.1.1` or `dnac.example.com`)
2. **Username** for API authentication
3. **Password** (input is hidden)

### Example Session

```
============================================================
Cisco Catalyst Center - License Report Generator
============================================================

Catalyst Center hostname or IP: 10.1.1.1
Enter username: admin
Enter password: 
Authenticating...
✓ Authentication successful

Retrieving devices...
✓ Found 150 total devices
  Retrieved 150/150 devices
✓ Retrieved all 150 devices

Filtering unregistered devices...
✓ Filtered 23 unregistered devices

Generating PDF report...
✓ PDF report generated: unregistered_devices_20260511_143022.pdf

============================================================
Report complete: unregistered_devices_20260511_143022.pdf
============================================================
```

## Output

The script generates a PDF file named `unregistered_devices_YYYYMMDD_HHMMSS.pdf` in the current working directory.

The report uses landscape A4 format with Cisco branding and contains a table with three columns:

| Column | Description |
|--------|-------------|
| Device Name | Hostname of the device (truncated to 30 characters) |
| IP Address | Management IP address |
| Network License | Current network licence level |

## API Reference

The script calls two Catalyst Center REST API endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/dna/system/api/v1/auth/token` | POST | Authenticate via Basic Auth, returns a token |
| `/dna/intent/api/v1/licenses/device/summary` | GET | Retrieve licence device summary with pagination |

The device summary endpoint accepts these query parameters:

- `page_number` ... page index (starts at 1)
- `limit` ... devices per page (set to 500)
- `order` ... sort direction (`asc`)
- `sort_by` ... sort field (`device_name`)

For full API documentation, see the [Cisco Catalyst Center API Reference](https://developer.cisco.com/docs/dna-center/).

## SSL Verification

The script disables SSL certificate verification by default. This is common in lab and production environments where Catalyst Center uses self-signed certificates. The `urllib3` InsecureRequestWarning is also suppressed to keep the output clean.

If your environment uses trusted certificates and you want to enable verification, change `verify=False` to `verify=True` in both API calls within the script.

## Error Handling

The script handles several failure scenarios gracefully:

- **Authentication failure**: Prints a descriptive error message and exits
- **Connection timeout**: All API calls enforce a 10-second timeout
- **Zero matching devices**: Exits cleanly with an informational message ("No unregistered devices found.")
- **Missing dependencies**: If `requests` or `fpdf2` aren't installed, the script prints install instructions and exits before doing anything else

## Author

Martyn Rees

## Licence

MIT License
