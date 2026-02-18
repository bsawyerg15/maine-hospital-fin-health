import pdfplumber
import pandas as pd
import re
import numpy as np
import sys

# Path to the PDF file and output base
pdf_path = sys.argv[1] if len(sys.argv) > 1 else 'src/z_Data/Raw_Data/Report_B_FY24_All_Financial_Hosp_251231.pdf'
output_base = sys.argv[2] if len(sys.argv) > 2 else 'hospital'

# Function to clean dollar values
def clean_dollar_value(value):
    if pd.isna(value) or value == '' or value == '' or value == '-' or value == '(cid:132)':
        return np.nan
    value = str(value).strip()
    if value.startswith('(') and value.endswith(')'):
        # Negative value
        inner = value[1:-1]
        num_str = re.sub(',', '', inner)
        try:
            return -float(num_str)
        except ValueError:
            return np.nan
    else:
        num_str = re.sub(',', '', value)
        try:
            return float(num_str)
        except ValueError:
            return np.nan

# Open the PDF
with pdfplumber.open(pdf_path) as pdf:
    data = []
    current_hospital = None
    start_parsing = False
    years = ['2020', '2021', '2022', '2023', '2024']  # default

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

            # Get hospital name from first line
            first_line = lines[0].strip()
            hospital_name = re.sub(r'\s*\(continued\)$', '', first_line).strip()

            # Update current hospital
            if "(continued)" in first_line:
                # Continuation page, keep current_hospital
                pass
            else:
                # New hospital
                current_hospital = hospital_name
                print(f"Processing {hospital_name}")

            # Check if this page has data to parse
            if 'DATA ELEMENTS' in text:
                start_parsing = True
            should_parse = 'DATA ELEMENTS' in text or (current_hospital == hospital_name and 'RATIOS' not in text)

            if should_parse and start_parsing:
                # Parse the DATA ELEMENTS section
                in_data = should_parse  # True for both first and continuation pages
                for line in lines:
                    line = line.strip()
                    if 'DATA ELEMENTS' in line:
                        in_data = True
                        continue
                    elif in_data:
                        if line.startswith('FY '):
                            years = line.split()[1:]
                            continue
                        elif not line or 'RATIOS' in line:
                            if 'RATIOS' in line:
                                current_hospital = None  # Stop for this hospital
                                break
                            continue
                        # Parse the data line
                        parts = line.split()
                        if len(parts) >= 2:
                            # Find the index of the first value (numeric or starts with '(')
                            value_start = None
                            for i, part in enumerate(parts):
                                if re.match(r'^-?\d', part) or part.startswith('(') or part in ['-', '', '(cid:132)']:
                                    value_start = i
                                    break
                            if value_start is not None and value_start > 0:
                                measure = ' '.join(parts[:value_start])
                                value_parts = parts[value_start:]
                                # Pad or truncate to 5 values
                                while len(value_parts) < 5:
                                    value_parts.append(np.nan)
                                value_parts = value_parts[:5]
                                values = [clean_dollar_value(v) for v in value_parts]
                                # Append
                                data_dict = {'Hospital': current_hospital, 'Measure': measure}
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
df.set_index(['Hospital', 'Measure'], inplace=True)

print(f"Successfully extracted {len(df)} data element records from {len(df.index.levels[0])} hospitals")
print("\nDataFrame shape:", df.shape)
print("\nSample of the data:")
print(df.head(20))

# Save to CSV
df.to_csv(f'src/z_Data/Preprocessed_Data/{output_base}_dollar_elements.csv')
print(f"\nSaved to src/z_Data/Preprocessed_Data/{output_base}_dollar_elements.csv")

# Save to pickle
df.to_pickle(f'src/z_Data/Preprocessed_Data/{output_base}_dollar_elements.pkl')
print(f"Saved to src/z_Data/Preprocessed_Data/{output_base}_dollar_elements.pkl")
