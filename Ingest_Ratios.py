import pdfplumber
import pandas as pd
import re
import sys

# Path to the PDF file and output base
pdf_path = sys.argv[1] if len(sys.argv) > 1 else 'src/z_Data/Raw_Data/Report_B_FY24_All_Financial_Hosp_251231.pdf'
output_base = sys.argv[2] if len(sys.argv) > 2 else 'hospital'
max_pad = 4 if 'health' in output_base else 5

# Function to clean ratio values
def clean_value(value):
    if pd.isna(value) or value == '' or value == '' or value == '-' or value == '(cid:132)' or value == 'Ä†' or value == '†' or value in ['N/A', 'n/a', 'NA', 'na']:
        return None
    value = str(value).strip()
    if value.startswith('(') and value.endswith(')'):
        # Negative value
        inner = value[1:-1]
        # Remove common units
        inner = re.sub(r'(rate|days|years|%)$', '', inner)
        # Extract numeric part
        match = re.search(r'[-+]?\d*\.?\d+', inner)
        if match:
            try:
                return -float(match.group())
            except ValueError:
                return None
        return None
    else:
        # Remove common units
        value = re.sub(r'(rate|days|years|%)$', '', value)
        # Extract numeric part
        match = re.search(r'[-+]?\d*\.?\d+', value)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None

# Open the PDF
with pdfplumber.open(pdf_path) as pdf:
    data = []
    current_hospital = None
    start_parsing = False
    printed = False
    years = ['2020', '2021', '2022', '2023', '2024']  # default
    years_parsed = False

    # Iterate through all pages
    for page_num, page in enumerate(pdf.pages):
        try:
            # Extract text
            text = page.extract_text()
            if not text:
                continue

            lines = text.split('\n')
            if not lines:
                continue

            # Get hospital name from third or fourth line
            first_line = lines[0].strip()

            # Update current hospital
            if "(continued)" in first_line:
                # Continuation page, keep current_hospital
                pass
            else:
                # New hospital
                third_line = lines[2].strip() if len(lines) > 2 else ""
                fourth_line = lines[3].strip() if len(lines) > 3 else ""
                # Use the line that contains " -- "
                if " -- " in third_line:
                    hospital_line = third_line
                elif " -- " in fourth_line:
                    hospital_line = fourth_line
                else:
                    hospital_line = third_line  # fallback
                hospital_name = hospital_line.split(" -- ")[0].strip() if " -- " in hospital_line else hospital_line
                current_hospital = hospital_name
                print(f"Processing {hospital_name}")

            # Check if this page has data to parse
            if 'RATIOS' in text:
                start_parsing = True
                if not printed:
                    print(f"\n--- Raw text of page {page_num} with RATIOS ---\n{text}\n--- End ---\n")
                    printed = True
            should_parse = 'RATIOS' in text or (current_hospital == hospital_name and start_parsing)

            if should_parse and start_parsing:
                # Parse years if not already parsed
                if not years_parsed:
                    for ln in lines:
                        ln = ln.strip()
                        if 'FY' in ln:
                            parts = ln.split()
                            years = [p for p in parts if p.isdigit() and len(p) == 4][:5]
                            years_parsed = True
                            break

                # Parse the RATIOS section
                current_category = None
                in_ratios = False

                for line in lines:
                    line = line.strip()
                    if 'RATIOS' in line:
                        in_ratios = True
                        continue
                    if in_ratios:
                        if not line:
                            continue
                        # Check if it's a category header (no numbers)
                        if not re.search(r'\d', line) and len(line) > 3:
                            current_category = line
                            continue
                        # Check if it's a ratio line (contains numbers)
                        elif re.search(r'\d', line):
                            # Flexible parsing: find first numeric part
                            parts = line.split()
                            if len(parts) >= 2:
                                value_start = None
                                special_chars = ['†', '', '-', '(cid:132)', 'Ä†', 'N/A', 'n/a', 'NA', 'na']
                                for i, part in enumerate(parts):
                                    if re.match(r'^-?(\d|\.)|\(', part) or part in special_chars:
                                        value_start = i
                                        break
                                if value_start is not None and value_start > 0:
                                    # Check if previous is unit
                                    units = ['rate', 'days', 'years']
                                    if value_start > 1 and parts[value_start - 1] in units:
                                        ratio_name = ' '.join(parts[:value_start - 1])
                                    else:
                                        ratio_name = ' '.join(parts[:value_start])
                                    # Skip header lines
                                    if 'FY' in ratio_name or 'Unit' in ratio_name or 'Consolidated' in ratio_name:
                                        continue
                                    value_parts = parts[value_start:]
                                    # Pad or truncate to max_pad values
                                    while len(value_parts) < max_pad:
                                        value_parts.append(None)
                                    value_parts = value_parts[:max_pad]
                                    values = [clean_value(v) for v in value_parts]
                                    # Append
                                    data_dict = {'Hospital': current_hospital, 'Ratio': ratio_name}
                                    for i, val in enumerate(values):
                                        col = f'FY {years[i] if i < len(years) else str(2020 + i)}'
                                        data_dict[col] = val
                                    data.append(data_dict)
        except Exception as e:
            print(f"Error processing page {page_num + 1}: {e}")
            continue

# Create DataFrame
df = pd.DataFrame(data)

# Set multi-index
df.set_index(['Hospital', 'Ratio'], inplace=True)

print(f"Successfully extracted {len(df)} ratio records from {len(df.index.levels[0])} hospitals")
print("\nDataFrame shape:", df.shape)
print("\nSample of the data:")
print(df.head(10))

# Save to CSV
df.to_csv(f'src/z_Data/Preprocessed_Data/{output_base}.csv')
print(f"\nSaved to src/z_Data/Preprocessed_Data/{output_base}.csv")
