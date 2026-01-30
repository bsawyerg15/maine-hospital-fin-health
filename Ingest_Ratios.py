import pdfplumber
import pandas as pd
import re

# Path to the PDF file
pdf_path = 'z_Data/Raw_Data/Report_B_FY24_All_Financial_Hosp_251231.pdf'

# Function to clean ratio values
def clean_value(value):
    if pd.isna(value) or value == '':
        return None
    # Remove units and extra text
    value = str(value).strip()
    # Remove common units
    value = re.sub(r'(rate|days|years|%)$', '', value)
    # Extract numeric part
    match = re.search(r'[-+]?\d*\.?\d+', value)
    if match:
        return float(match.group())
    return None

# Open the PDF
with pdfplumber.open(pdf_path) as pdf:
    data = []

    # Iterate through all pages
    for page_num, page in enumerate(pdf.pages):
        try:
            # Extract text
            text = page.extract_text()
            if not text:
                continue

            # Check if page contains RATIOS
            if 'RATIOS' in text:
                lines = text.split('\n')
                if not lines:
                    continue

                # Get hospital name from first line
                first_line = lines[0].strip()
                hospital_name = re.sub(r'\s*\(continued\)$', '', first_line).strip()

                # Find the RATIOS section and parse the lines
                in_ratios = False
                current_category = None

                for line in lines:
                    line = line.strip()
                    if line == 'RATIOS':
                        in_ratios = True
                        continue
                    elif in_ratios:
                        if not line:
                            continue
                        # Check if it's a category header (no numbers)
                        if not re.search(r'\d', line) and len(line) > 3:
                            current_category = line
                            continue
                        # Check if it's a ratio line (contains numbers)
                        elif re.search(r'\d', line):
                            # Parse ratio line like "Total Margin6.94%12.47%16.10%24.09%8.19%"
                            # Find the ratio name and values
                            parts = re.split(r'(\d+\.?\d*%?)', line)
                            if len(parts) >= 11:  # Name + 5 values + units
                                ratio_name = parts[0].strip()
                                values = []
                                for i in range(1, 11, 2):  # Take numeric parts
                                    if i < len(parts):
                                        val = clean_value(parts[i])
                                        values.append(val)

                                if len(values) >= 5 and ratio_name:
                                    data.append({
                                        'Hospital': hospital_name,
                                        'Ratio': ratio_name,
                                        'FY 2020': values[0],
                                        'FY 2021': values[1],
                                        'FY 2022': values[2],
                                        'FY 2023': values[3],
                                        'FY 2024': values[4]
                                    })
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
df.to_csv('hospital_ratios.csv')
print("\nSaved to hospital_ratios.csv")

# Save to pickle
df.to_pickle('hospital_ratios.pkl')
print("Saved to hospital_ratios.pkl")
