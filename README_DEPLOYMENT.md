# HPV Tracker Pro — Windows Portable App

## Overview
This is a self-contained portable Windows build of HPV Tracker Pro. No Python installation or additional dependencies are required. Simply copy the folder and run the `.exe` — no extraction delay on startup.

## Files Included
```
HPV_Tracker_Pro/
├── HPV_Tracker_Pro.exe      ← Main application executable
├── icons/                   ← Optional 16x16 PNG icons
├── _internal/               ← Runtime libraries (do not delete)
└── README_DEPLOYMENT.md     ← This file
```

> **Important:** Keep all files in the `HPV_Tracker_Pro` folder together. The `.exe` will not run if moved out on its own.

## System Requirements
- Windows 10 or later (64-bit)
- Minimum 150 MB free disk space
- No additional software required

## Installation
1. Copy the entire `HPV_Tracker_Pro` folder to a location of your choice (e.g. your Desktop or a USB drive).
2. Double-click `HPV_Tracker_Pro.exe` to run the application.
3. The application will create its configuration file and database in the same folder on first run.

## First Run
On first launch, the application will:
- Create `hpv_tracker_config.json` (configuration file)
- Create `hpv_samples.db` (SQLite database)
- Set up the default backup directory in your Documents folder

## Data Storage
- Database: `hpv_samples.db` (SQLite format, stored next to the `.exe`)
- Configuration: `hpv_tracker_config.json`
- Backups: Default location is `~/Documents/HPV_Tracker_Backups/`

## Features
- **Sample Management**: Add, edit, delete HPV samples with unique episode barcodes
- **Search & Filter**: Real-time search across all sample data
- **Import Data**: Import from CSV files or other SQLite databases
- **Export Options**:
  - CSV format for spreadsheet applications
  - PDF format — A4, 3 trays/page, CHECKED BY / RECEIVED BY sign-off, NHLS disclaimer footer
  - DOCX format — matching A4 layout for Microsoft Word
- **Database Backup**: Create timestamped backups of your data
- **Audit Logging**: Complete tracking of all operations
- **Keyboard Shortcuts**:
  - `Enter` — Add sample
  - `Delete` — Delete selected samples
  - `Double-click` — Edit sample
  - `Escape` — Cancel dialogs

## Moving Your Data
To move the app or your data to another computer:
1. Copy the entire `HPV_Tracker_Pro` folder, **or**
2. Copy just `hpv_samples.db` and `hpv_tracker_config.json` into the new installation folder.

## Icon Support (Optional)
Place 16×16 PNG icon files in the `icons/` subfolder:
- `add.png`, `edit.png`, `delete.png`, `search.png`
- `export.png`, `import.png`, `backup.png`, `reset.png`
- `csv.png`, `pdf.png`, `docx.png`, `database.png`

Icons are loaded automatically at startup.

## Troubleshooting
- **Application won't start**: Ensure the entire `HPV_Tracker_Pro` folder is intact and that `_internal/` has not been deleted or moved.
- **Import errors**: Check that CSV files have episode barcodes in the first column.
- **Export issues**: Ensure the application folder is writable (not on a read-only drive).
- **Database errors**: Check that the application folder is writable.

## Security Notes
- No network connections are made
- All data is stored locally
- No personal information is transmitted
- Audit logs contain only system usernames and timestamps

## Version Information
- Application: HPV Tracker Pro
- Build Mode: Portable folder (onedir) — fast startup, no extraction required
- Platform: Windows 64-bit
- Dependencies: All included (Python, Tkinter, ReportLab, python-docx, Pillow)