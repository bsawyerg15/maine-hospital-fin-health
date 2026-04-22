# Adding a New Year of Maine Data

## Prerequisites

Open this project in an IDE (interactive development environment) such as VS Code (free from Microsoft and easy to use). All terminal commands below should be run in VS Code's integrated terminal — open it with `` Ctrl+` `` (Windows) or `` Cmd+` `` (Mac), or via the menu: **Terminal → New Terminal**.

The terminal will open at the project root automatically.

Follow the instructions by hand or this should be a trivial task for AI code assist.

---

## 1. Download the new PDF and load it into the project.

In the VS Code file explorer (left sidebar), navigate to:

```
src/z_Data/Raw_Data/ME/ME_Hospital/
```

Copy the new MHDO hospital financial report PDF into that folder (you can drag and drop it from your file manager).

---

## 2. Run the two preprocessing scripts

In the integrated terminal (instructions for opening in prerequisites section), navigate to the `src/` folder:

```bash
cd src
```

Then run both scripts below. Replace `<new_report>.pdf` with the actual filename of the PDF you added, and replace `<YYYY_YYYY>` with the year range covered by the report (e.g. `2025_2029`).

**Dollar line items** (balance sheet and income statement figures):
```bash
python -m b_Ingest.me_preprocessing.ingest_dollar_elements \
  z_Data/Raw_Data/ME/ME_Hospital/<new_report>.pdf \
  hospital_dollar_elements_<YYYY_YYYY>
```

**Financial ratios:**
```bash
python -m b_Ingest.me_preprocessing.ingest_ratios \
  z_Data/Raw_Data/ME/ME_Hospital/<new_report>.pdf \
  hospital_ratios_<YYYY_YYYY>
```

Each script will print the name of each hospital as it processes it, and save a `.csv` file to `src/z_Data/Preprocessed_Data/` when done.

---

## 3. Register the new CSVs

In the VS Code file explorer, open:

```
src/b_Ingest/z_get_financials_by_state.py
```

Find the section that looks like this:

```python
_ME_HOSPITAL_FILES = [
    "hospital_dollar_elements_2005_2009.csv",
    ...
    "hospital_ratios_2020_2024.csv",
]
```

Add the two new filenames to the end of that list (before the closing `]`):

```python
    "hospital_dollar_elements_<YYYY_YYYY>.csv",
    "hospital_ratios_<YYYY_YYYY>.csv",
```

Save the file (`Cmd+S` or `Ctrl+S`).

---

## 4. Push to GitHub

Open the **Source Control** panel in VS Code (click the branch icon in the left sidebar, or press `Ctrl+Shift+G` / `Cmd+Shift+G`).

1. You should see the new PDF, the two new CSVs, and the updated `z_get_financials_by_state.py` listed under **Changes**.
2. Click the **+** next to each file (or next to **Changes** to stage all at once).
3. Type a commit message in the box at the top, e.g. `Add Maine data <YYYY_YYYY>`.
4. Click **Commit**, then **Sync Changes** to push to GitHub.

The app will automatically redeploy. After a minute or two, visit the live app to confirm the new year's data appears in the charts and tables.
