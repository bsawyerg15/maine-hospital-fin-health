import re


def parse_hospital_name(lines: list[str], current_hospital: str | None) -> str | None:
    first_line = lines[0].strip() if lines else ""
    if "(continued)" in first_line:
        return current_hospital
    third_line = lines[2].strip() if len(lines) > 2 else ""
    fourth_line = lines[3].strip() if len(lines) > 3 else ""
    if " -- " in third_line:
        hospital_line = third_line
    elif " -- " in fourth_line:
        hospital_line = fourth_line
    else:
        hospital_line = third_line
    return hospital_line.split(" -- ")[0].strip() if " -- " in hospital_line else hospital_line


def parse_years(lines: list[str]) -> list[str] | None:
    for ln in lines:
        ln = ln.strip()
        if 'FY' in ln:
            parts = ln.split()
            years = [p for p in parts if p.isdigit() and len(p) == 4][:5]
            if years:
                return years
    return None
