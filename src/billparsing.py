import re

# Function to clean the invoice text (join broken item lines)


def clean_invoice_text(text):
    text = text.replace(',', '')  # remove commas in numbers
    lines = text.strip().split('\n')
    cleaned_lines = []
    buffer = ""

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Join broken item lines
        if re.search(r'(\d+\s+)?\d+(\.\d+)?\s+\d+(\.\d+)?$', line):
            if buffer:
                cleaned_lines.append(buffer.strip())
                buffer = ""
            cleaned_lines.append(line)
        else:
            if buffer:
                # Check if this line might be a continuation of an item description
                if not re.match(r'(Sub Total|Total|CGST|SGST|Tax|Invoice)', line, re.IGNORECASE):
                    buffer += " " + line
                else:
                    cleaned_lines.append(buffer.strip())
                    buffer = ""
                    cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)

    if buffer:
        cleaned_lines.append(buffer.strip())

    return cleaned_lines


# Function to extract items, taxes, and total information from the invoice text
def extract_invoice_data(text):
    lines = clean_invoice_text(text)
    items = {}  # Initialize as empty dictionary
    taxes = {}  # Initialize as empty dictionary
    total = 0   # Default to 0 instead of None
    subtotal = 0  # Default to 0 instead of None

    # Regex patterns for full item lines and taxes/total
    # Updated item pattern to be more flexible
    full_item_pattern = re.compile(
        r'^(.*?)\s+(\d+)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)$')

    # More flexible tax patterns to handle various formats
    # This will match both standard "CGST @2.5% : 16.80" and also "CGST@z2.5 25.89" format
    cgst_pattern = re.compile(
        r'CGST\s*@\s*[zZ]?\s*\d+(?:\.\d+)?%?\s*[:\-]?\s*(\d+(?:\.\d+)?)')
    sgst_pattern = re.compile(
        r'SGST\s*@\s*[zZ]?\s*\d+(?:\.\d+)?%?\s*[:\-]?\s*(\d+(?:\.\d+)?)')

    # Also add patterns for tax values without percentages
    simple_cgst_pattern = re.compile(r'CGST\s*[:\-]?\s*(\d+(?:\.\d+)?)')
    simple_sgst_pattern = re.compile(r'SGST\s*[:\-]?\s*(\d+(?:\.\d+)?)')

    subtotal_pattern = re.compile(r'Sub\s*Total\s*[:\-]?\s*(\d+(?:\.\d+)?)')
    total_pattern = re.compile(r'(?:^|\s)Total\s*[:\-]?\s*(\d+(?:\.\d+)?)')

    # Extracting items (food) and their quantities and amounts
    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Try all patterns for CGST
        cgst_match = cgst_pattern.search(line)
        if not cgst_match:
            cgst_match = simple_cgst_pattern.search(line)
        if cgst_match:
            taxes['CGST'] = float(cgst_match.group(1))
            continue

        # Try all patterns for SGST
        sgst_match = sgst_pattern.search(line)
        if not sgst_match:
            sgst_match = simple_sgst_pattern.search(line)
        if sgst_match:
            taxes['SGST'] = float(sgst_match.group(1))
            continue

        # Check for subtotal
        subtotal_match = subtotal_pattern.search(line)
        if subtotal_match:
            subtotal = float(subtotal_match.group(1))
            continue

        # Check for total (more specific pattern to avoid matching "Sub Total")
        total_match = total_pattern.search(line)
        if total_match and not subtotal_pattern.search(line):
            total = float(total_match.group(1))
            continue

        # Match items with qty, rate, and amount
        match = full_item_pattern.match(line)
        if match:
            name = match.group(1).strip()
            qty = int(match.group(2))
            rate = float(match.group(3))
            amount = float(match.group(4))
            items[name] = {"qty": qty, "amount": amount}
            continue

        # Additional pattern for items without qty column but with amount (special case)
        no_qty_full_item = re.compile(
            r'^(.*?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)$')
        match = no_qty_full_item.match(line)
        if match and not re.search(r'(CGST|SGST|Total)', match.group(1)):
            name = match.group(1).strip()
            # Try to infer qty by dividing amount by rate
            rate = float(match.group(2))
            amount = float(match.group(3))
            inferred_qty = round(amount / rate) if rate > 0 else 1
            items[name] = {"qty": inferred_qty, "amount": amount}
            continue

    # If we have a total but no subtotal, use the total as subtotal
    if not subtotal and total:
        subtotal = total

    # If we have a subtotal but no total, use the subtotal as total
    if not total and subtotal:
        total = subtotal

    # Final check to ensure everything is the right type
    if not isinstance(items, dict):
        items = {}
    if not isinstance(taxes, dict):
        taxes = {}
    if total is None:
        total = 0

    return {
        "items": items,
        "taxes": taxes,
        "total": total
    }
