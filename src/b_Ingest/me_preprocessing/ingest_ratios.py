import re
import sys
import pandas as pd
from b_Ingest.me_preprocessing.pdf_parse_helpers import parse_hospital_name, parse_years
import pdfplumber


def ingest_ratios(pdf_path: str, output_base: str) -> pd.DataFrame:
    max_pad = 4 if 'health' in output_base else 5

    def clean_value(value):
        if pd.isna(value) or value in ('', '-', '(cid:132)', 'Ä†', '†', 'N/A', 'n/a', 'NA', 'na'):
            return None
        value = str(value).strip()
        if value.startswith('(') and value.endswith(')'):
            inner = re.sub(r'(rate|days|years|%)$', '', value[1:-1])
            match = re.search(r'[-+]?\d*\.?\d+', inner)
            return -float(match.group()) if match else None
        value = re.sub(r'(rate|days|years|%)$', '', value)
        match = re.search(r'[-+]?\d*\.?\d+', value)
        return float(match.group()) if match else None

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

                if 'RATIOS' in text:
                    start_parsing = True
                should_parse = 'RATIOS' in text or (current_hospital and start_parsing)

                if should_parse and start_parsing:
                    if not years_parsed:
                        parsed = parse_years(lines)
                        if parsed:
                            years = parsed
                            years_parsed = True

                    in_ratios = False
                    current_category = None
                    for line in lines:
                        line = line.strip()
                        if 'RATIOS' in line:
                            in_ratios = True
                            continue
                        if not in_ratios:
                            continue
                        if not line:
                            continue
                        if not re.search(r'\d', line) and len(line) > 3:
                            current_category = line
                            continue
                        if re.search(r'\d', line):
                            parts = line.split()
                            if len(parts) < 2:
                                continue
                            value_start = None
                            special_chars = ['†', '', '-', '(cid:132)', 'Ä†', 'N/A', 'n/a', 'NA', 'na']
                            for i, part in enumerate(parts):
                                if re.match(r'^-?(\d|\.)|\(', part) or part in special_chars:
                                    value_start = i
                                    break
                            if value_start is None or value_start == 0:
                                continue
                            units = ['rate', 'days', 'years']
                            if value_start > 1 and parts[value_start - 1] in units:
                                ratio_name = ' '.join(parts[:value_start - 1])
                            else:
                                ratio_name = ' '.join(parts[:value_start])
                            if any(kw in ratio_name for kw in ('FY', 'Unit', 'Consolidated')):
                                continue
                            value_parts = parts[value_start:]
                            while len(value_parts) < max_pad:
                                value_parts.append(None)
                            value_parts = value_parts[:max_pad]
                            values = [clean_value(v) for v in value_parts]
                            row = {'Organization': current_hospital, 'Measure': ratio_name}
                            for i, val in enumerate(values):
                                row[f'FY {years[i] if i < len(years) else str(2020 + i)}'] = val
                            data.append(row)
            except Exception as e:
                print(f"Error processing page {page_num + 1}: {e}")

    df = pd.DataFrame(data).set_index(['Organization', 'Measure'])
    print(f"Successfully extracted {len(df)} ratio records from {len(df.index.levels[0])} hospitals")
    df.to_csv(f'src/z_Data/Preprocessed_Data/{output_base}.csv')
    print(f"Saved to src/z_Data/Preprocessed_Data/{output_base}.csv")
    return df


if __name__ == '__main__':
    _pdf_path = sys.argv[1] if len(sys.argv) > 1 else 'src/z_Data/Raw_Data/ME/ME_Hospital/Report_B_FY24_All_Financial_Hosp_251231.pdf'
    _output_base = sys.argv[2] if len(sys.argv) > 2 else 'hospital'
    ingest_ratios(_pdf_path, _output_base)
