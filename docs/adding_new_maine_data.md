# Adding a New Year of Maine Data

## Prerequisites

### Install VSCode or another IDE (Interactiive Development Environment)
VSCode is an example of a coding evironment and is a free software owned by Microsoft that will prevent you from having to interact with the terminal. I would highly suggest using an IDE for any of the following steps though it's not strictly necessary and everything can be done in the terminal if preferred.

### First time setup: clone the project

If you don't already have the project on your computer, you'll need to clone (download) it from GitHub. Open VS Code and follow these steps:

1. Open the **Source Control** panel (`Ctrl+Shift+G` / `Cmd+Shift+G`) and click **Clone Repository**, or open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and type **Git: Clone**.
2. Paste in the repository URL: `https://github.com/bsawyerg15/maine-hospital-fin-health.git`
3. Choose a folder on your computer to save it in.
4. When prompted, click **Open** to open the cloned project.

### Uploading New Data

Open this project in VSCode. All terminal commands below should be run in VS Code's integrated terminal — open it with `` Ctrl+` `` (Windows) or `` Cmd+` `` (Mac), or via the menu: **Terminal → New Terminal**.

The terminal will open at the project root automatically.

Follow the instructions by hand or give it to an AI code assist -- it should be a trivial task for it.

Caveat: these steps below will only work if the reporting format of the pdfs hasn't changed. To the extent they do, the ingest script will need to be reworked. Again, AI code assists seem capable of this task.

---

## 1. Download the new PDF and load it into the project.

In the VS Code file explorer (left sidebar), navigate to:

```
src/z_Data/Raw_Data/ME/ME_Hospital/
```

Copy the new MHDO hospital financial report PDF into that folder (you can drag and drop it from your file manager).

---

## 2. Run the preprocessing scripts

In the integrated terminal (instructions for opening in prerequisites section), navigate to the `src/` folder:

```bash
cd src
```

Replace `<new_report>.pdf` with the actual filename of the PDF you added, `<YYYY_YYYY>` with the year range covered by the report (e.g. `2025_2029`), and <ENTITY TYPE> with either 'health_systems' or 'hospital'.

**Dollar line items** (balance sheet and income statement figures):
```bash
python -m b_Ingest.me_preprocessing.ingest_dollar_elements \
  z_Data/Raw_Data/ME/ME_Hospital/<new_report>.pdf \
  <ENTITY TYPE>_dollar_elements_<YYYY_YYYY>
```

**Financial ratios:**
```bash
python -m b_Ingest.me_preprocessing.ingest_ratios \
  z_Data/Raw_Data/ME/ME_Hospital/<new_report>.pdf \
  <ENTITY TYPE>_ratios_<YYYY_YYYY>
```

Each script will print the name of each entity as it processes it, and save a `.csv` file to `src/z_Data/Preprocessed_Data/` when done.

---

## 3. Register the new CSVs

In the VS Code file explorer, open:

```
src/b_Ingest/z_get_financials_by_state.py
```

### If adding hospital data

Find `_ME_HOSPITAL_FILES` and add the new filenames to the end of the list (before the closing `]`):

```python
    "hospital_dollar_elements_<YYYY_YYYY>.csv",
    "hospital_ratios_<YYYY_YYYY>.csv",
```

### If adding health system data

Find `_ME_HEALTH_SYSTEMS_FILES` and add the new filename to the end of the list:

```python
    "health_systems_dollar_elements_<YYYY_YYYY>.csv",
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

---

## Troubleshooting: data appears in preprocessed CSVs but not in the dashboards

If you can see data in the preprocessed CSVs (in `src/z_Data/Preprocessed_Data/`) but it isn't showing up in the dashboards, the most likely cause is that a measure name or hospital name in the new PDF doesn't exactly match what the project expects/how things were reported previously. Two lookup CSVs control this mapping.

### Fix missing measures — `clean_measure_names.csv`

This step will rename measures that show up differently than before (including things like spelling differences, extra spaces, or punctuation).

Open `src/a_Config/csv_configs/clean_measure_names.csv`. It has three columns:

| Column | Meaning |
|---|---|
| `State` | `ME` or `MA` |
| `As Reported` | The exact string that appears in the raw PDF/CSV |
| `Standardized` | The internal name the project uses |

**When to update:** a measure appears in a preprocessed CSV but is absent from the dashboards. This usually happens because the PDF used a slightly different label (e.g. a trailing space, a unit suffix like `days`, or a different spelling).

**How to fix:**

1. Open the preprocessed CSV generated in step 2. Find the measure name exactly as it was extracted.
2. Check whether that name already appears in the `As Reported` column of `clean_measure_names.csv`. If it does, there is a different issue.
3. If it is **not** listed, add a new row:
   ```
   ME,<exact string from the preprocessed CSV>,<matching Standardized name>
   ```
   The `Standardized` value must exactly match an existing entry in `src/a_Config/csv_configs/fin_statement_model.csv`.
4. Save, commit, and push the file. The app will redeploy with the fix.

### Fix missing hospitals — `hospital_renames_me.csv`

Open `src/a_Config/csv_configs/hospital_renames_me.csv`. It has two columns:

| Column | Meaning |
|---|---|
| `As Reported` | The exact hospital name that appears in the raw PDF |
| `Standardized` | The internal name the pipeline uses |

**When to update:** a hospital appears in a preprocessed CSV but is absent from the dashboards, or shows up under an unexpected name. This usually happens when a hospital has been renamed or rebranded between reporting periods.

**How to fix:**

1. Open the preprocessed CSV and find the hospital name exactly as it was extracted (it is also printed to the terminal as each entity is processed in step 2).
2. Open `src/a_Config/csv_configs/hospital_metadata.csv` and find the canonical name for that hospital.
3. Add a new row to `hospital_renames_me.csv`:
   ```
   <exact string from the preprocessed CSV>,<canonical name from hospital_metadata.csv>
   ```
4. Save, commit, and push the file. The app will redeploy with the fix.
