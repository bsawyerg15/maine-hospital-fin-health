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
    if pd.isna(value) or value == '':
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
    if 'health' in output_base:
        years = ['2021', '2022', '2023', '2024']
    else:
        years = ['2020', '2021', '2022', '2023', '2024']

    # Iterate through all pages
    for page_num, page in enumerate(pdf.pages):
        try:
            # Extract text
            text = page.extract_text()
            if not text:
                continue

            # Get hospital name from first line
            lines = text.split('\n')
            if not lines:
                continue
            first_line = lines[0].strip()
            hospital_name = re.sub(r'\s*\(continued\)$', '', first_line).strip()

            # Update current hospital
            if "(continued)" in first_line:
                pass
            else:
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
                # Parse the RATIOS section
                in_ratios = 'RATIOS' in text
                current_category = None

                for line in lines:
                    line = line.strip()
                    if line == 'RATIOS':
                        in_ratios = True
                        continue
                    elif in_ratios:
                        if line.startswith('FY '):
                            years = line.split()[1:]
                            # Extend years if needed
                            while len(years) < max_pad:
                                years.append(str(int(years[-1]) + 1))
                            continue
                        elif not line:
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
                                for i, part in enumerate(parts):
                                    if re.match(r'^-?\d|\(', part):
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
df.to_csv(f'src/z_Data/Preprocessed_Data/{output_base}_ratios.csv')
print(f"\nSaved to src/z_Data/Preprocessed_Data/{output_base}_ratios.csv")

# Save to pickle
df.to_pickle(f'src/z_Data/Preprocessed_Data/{output_base}_ratios.pkl')
print(f"Saved to src/z_Data/Preprocessed_Data/{output_base}_ratios.pkl")
