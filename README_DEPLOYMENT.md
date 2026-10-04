# HPV Sample Tracker - Windows Executable

## Overview
This is a self-contained Windows executable of the HPV Sample Tracker application. No Python installation or additional dependencies are required.

## Files Included
- `HPV_Sample_Tracker.exe` - Main application executable (~35MB)
- `icons/` - Directory for optional 16x16 PNG icons
- `test_samples.csv` - Sample CSV file for testing import functionality
- `README_DEPLOYMENT.md` - This documentation file

## System Requirements
- Windows 10 or later (64-bit)
- Minimum 100MB free disk space
- No additional software required

## Installation
1. Extract all files to a folder of your choice
2. Double-click `HPV_Sample_Tracker.exe` to run the application
3. The application will create a configuration file and database in the same directory

## First Run
On first launch, the application will:
- Create `hpv_tracker_config.json` (configuration file)
- Create `hpv_samples.db` (SQLite database)
- Set up the default backup directory in your Documents folder

## Features
- **Sample Management**: Add, edit, delete HPV samples with unique episode barcodes
- **Search & Filter**: Real-time search across all sample data
- **Import Data**: Import from CSV files or other SQLite databases
- **Export Options**: 
  - CSV format for spreadsheet applications
  - PDF format with professional layout (90 entries per page, 3 trays of 30)
  - DOCX format for Microsoft Word
- **Database Backup**: Create timestamped backups of your data
- **Audit Logging**: Complete tracking of all operations
- **Keyboard Shortcuts**: 
  - Enter: Add sample
  - Delete: Delete selected samples
  - Double-click: Edit sample
  - Escape: Cancel dialogs

## Data Storage
- Database: `hpv_samples.db` (SQLite format)
- Configuration: `hpv_tracker_config.json`
- Backups: Default location is `~/Documents/HPV_Tracker_Backups/`

## Icon Support (Optional)
Place 16x16 PNG icon files in the `icons/` directory:
- `add.png`, `edit.png`, `delete.png`, `search.png`
- `export.png`, `import.png`, `backup.png`, `reset.png`
- `csv.png`, `pdf.png`, `docx.png`, `database.png`

Icons will be loaded automatically when the application starts.

## Testing the Application
1. Run `HPV_Sample_Tracker.exe`
2. Try adding a sample with episode barcode "TEST001"
3. Import the included `test_samples.csv` file
4. Export data to different formats (CSV, PDF, DOCX)
5. Test the search functionality
6. Create a database backup

## Troubleshooting
- **Application won't start**: Ensure you have Windows 10+ and sufficient disk space
- **Import errors**: Check that CSV files have episode barcodes in the first column
- **Export issues**: Ensure you have write permissions to the selected directory
- **Database errors**: Check that the application directory is writable

## Data Migration
To move your data to another computer:
1. Copy the entire application folder
2. Or copy just `hpv_samples.db` and `hpv_tracker_config.json`

## Support
This is a standalone application with no external dependencies. All functionality is self-contained within the executable.

## Version Information
- Application: HPV Sample Tracker v1.0
- Build Date: July 31, 2025
- Platform: Windows 64-bit
- Dependencies: All included (Python, Tkinter, ReportLab, python-docx, Pillow)

## Security Notes
- No network connections are made
- All data is stored locally
- No personal information is transmitted
- Audit logs contain only system usernames and timestamps