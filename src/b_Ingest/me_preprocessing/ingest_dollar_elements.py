import re
import sys
import numpy as np
import pandas as pd
from b_Ingest.me_preprocessing.pdf_parse_helpers import parse_hospital_name, parse_years
import pdfplumber


def ingest_dollar_elements(pdf_path: str, output_base: str) -> pd.DataFrame:
    def clean_dollar_value(value):
        if pd.isna(value) or value in ('', '-', '(cid:132)', 'Ä†', '†'):
            return np.nan
        value = str(value).strip()
        if value.startswith('(') and value.endswith(')'):
            try:
                return -float(re.sub(',', '', value[1:-1]))
            except ValueError:
                return np.nan
        try:
            return float(re.sub(',', '', value))
        except ValueError:
            return np.nan

    data = []
    current_hospital = None
    start_parsing = False
    years = ['2020', '2021', '2022', '2023', '2024']
    years_parsed = False

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            try:
                text = page.extract_text()
                if not text:
                    continue
                lines = text.split('\n')
                if not lines:
                    continue

                current_hospital = parse_hospital_name(lines, current_hospital)
                print(f"Processing {current_hospital}")

                if 'DATA ELEMENTS' in text:
                    start_parsing = True
                should_parse = 'DATA ELEMENTS' in text or (current_hospital and 'RATIOS' not in text)

                if should_parse and start_parsing:
                    if not years_parsed:
                        parsed = parse_years(lines)
                        if parsed:
                            years = parsed
                            years_parsed = True

                    in_data = False
                    for line in lines:
                        line = line.strip()
                        if 'DATA ELEMENTS' in line:
                            in_data = True
                            continue
                        if not in_data:
                            continue
                        if 'FY' in line:
                            continue
                        if not line:
                            continue
                        if 'RATIOS' in line:
                            break
                        parts = line.split()
                        if len(parts) < 2:
                            continue
                        value_start = None
                        for i, part in enumerate(parts):
                            if re.match(r'^-?\d', part) or part.startswith('(') or part in ('-', '', '(cid:132)', 'Ä†', '†'):
                                value_start = i
                                break
                        if value_start is None or value_start == 0:
                            continue
                        measure = ' '.join(parts[:value_start])
                        value_parts = parts[value_start:]
                        while len(value_parts) < 5:
                            value_parts.append(np.nan)
                        value_parts = value_parts[:5]
                        values = [clean_dollar_value(v) for v in value_parts]
                        row = {'Organization': current_hospital, 'Measure': measure}
                        for i, val in enumerate(values):
                            row[f'FY {years[i] if i < len(years) else str(2020 + i)}'] = val
                        data.append(row)
            except Exception as e:
                print(f"Error processing page {page_num + 1}: {e}")

    df = pd.DataFrame(data).set_index(['Organization', 'Measure'])
    print(f"Successfully extracted {len(df)} data element records from {len(df.index.levels[0])} hospitals")
    df.to_csv(f'src/z_Data/Preprocessed_Data/{output_base}_dollar_elements.csv')
    print(f"Saved to src/z_Data/Preprocessed_Data/{output_base}_dollar_elements.csv")
    return df


if __name__ == '__main__':
    _pdf_path = sys.argv[1] if len(sys.argv) > 1 else 'src/z_Data/Raw_Data/ME/ME_Hospital/Report_B_FY24_All_Financial_Hosp_251231.pdf'
    _output_base = sys.argv[2] if len(sys.argv) > 2 else 'hospital'
    ingest_dollar_elements(_pdf_path, _output_base)
