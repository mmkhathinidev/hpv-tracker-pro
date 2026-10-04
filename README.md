# HPV Tracker Pro

A professional desktop application for managing HPV sample records with comprehensive tracking, auditing, and export capabilities.

## Features

- **Sample Management**: Add, edit, and delete HPV samples with unique episode barcodes
- **Internal Reference System**: Auto-assigns sequential internal references to samples
- **Search & Filter**: Real-time search across all sample data
- **Import Data**: Import from CSV files or other SQLite databases
- **Export Options**:
  - CSV format for spreadsheet applications
  - PDF format with professional layout (90 entries per page, 3 trays of 30)
  - DOCX format for Microsoft Word
- **Database Backup**: Create timestamped backups of your data
- **Audit Logging**: Complete tracking of all operations with timestamps and user information
- **Configuration Management**: JSON-based configuration for customization
- **Keyboard Shortcuts**:
  - Enter: Add sample
  - Delete: Delete selected samples
  - Double-click: Edit sample
  - Escape: Cancel dialogs

## Screenshots

*(Add screenshots of the application interface here)*

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone this repository:
```bash
git clone https://github.com/mmkhathinidev/hpv-tracker-pro.git
cd hpv-tracker-pro
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python hpv_tracker.py
```

## Usage

### First Run

On first launch, the application will:
- Create `hpv_tracker_config.json` (configuration file)
- Create `hpv_samples.db` (SQLite database)
- Set up the default backup directory in your Documents folder

### Adding Samples

1. Enter an episode barcode in the "Episode barcode" field
2. Optionally set a starting internal reference number
3. Click "Assign Next" or press Enter
4. The sample will be added with an auto-incremented internal reference

### Editing Samples

- Double-click on any sample in the table to edit it
- Or select a sample and click "Edit Selected"

### Deleting Samples

- Select one or more samples in the table
- Click "Delete Selected" or press the Delete key
- Confirm the deletion

### Exporting Data

- **CSV**: Click "Export CSV" to save data in spreadsheet format
- **PDF**: Click "Export PDF" to generate a professional printable report
- **DOCX**: Click "Export DOCX" to create a Word document

### Importing Data

- Click "Import Database" to import from another SQLite database
- Click "Import CSV" to import from a CSV file

### Creating Backups

- Click "Backup Database" to create a timestamped backup
- Backups are saved to the configured backup directory

## Configuration

The application uses a JSON configuration file (`hpv_tracker_config.json`) with the following default settings:

```json
{
    "entries_per_page": 90,
    "database_file": "hpv_samples.db",
    "window_geometry": "900x700",
    "export_directory": "/home/user",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "ui_theme": "clam",
    "backup_directory": "/home/user/Documents/HPV_Tracker_Backups"
}
```

You can modify these settings to customize the application behavior.

## Building Standalone Executable

To create a standalone executable (Windows/Linux/macOS):

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Build the executable:
```bash
pyinstaller hpv_tracker.spec
```

3. The executable will be in the `dist/` directory

## Data Storage

- **Database**: `data/hpv_samples.db` (SQLite format)
- **Configuration**: `config/hpv_tracker_config.json`
- **Exports**: `exports/` directory for PDF, CSV, and DOCX files
- **Backups**: `backups/` directory for database backups
- **Audit Logs**: Stored in the database with full operation history

### Directory Structure

```
hpv-tracker-pro/
├── hpv_tracker_pro.py          # Main application
├── hpv_tracker_pro.spec        # PyInstaller configuration
├── requirements.txt             # Python dependencies
├── README.md                   # This file
├── README_DEPLOYMENT.md        # Deployment guide
├── LICENSE                     # MIT License
├── data/                       # Database files
│   └── hpv_samples.db         # Main database
├── config/                     # Configuration files
│   └── hpv_tracker_config.json # App configuration
├── exports/                    # Exported reports (PDF, CSV, DOCX)
├── backups/                    # Database backups
└── icons/                      # Optional UI icons
```

## Icon Support

Place 16x16 PNG icon files in the `icons/` directory:
- `add.png`, `edit.png`, `delete.png`, `search.png`
- `export.png`, `import.png`, `backup.png`, `reset.png`
- `csv.png`, `pdf.png`, `docx.png`, `database.png`

Icons will be loaded automatically when the application starts.

## Security Notes

- No network connections are made
- All data is stored locally
- No personal information is transmitted
- Audit logs contain only system usernames and timestamps
- Database uses SQLite with WAL mode for better performance and data integrity

## Troubleshooting

- **Application won't start**: Ensure Python 3.8+ is installed and dependencies are up to date
- **Import errors**: Check that CSV files have episode barcodes in the first column
- **Export issues**: Ensure you have write permissions to the selected directory
- **Database errors**: Check that the application directory is writable

## Data Migration

To move your data to another computer:
1. Copy the entire application folder including:
   - `data/` directory (contains the database)
   - `config/` directory (contains configuration)
   - `exports/` directory (contains exported reports)
   - `backups/` directory (contains database backups)
2. Or copy just `data/hpv_samples.db` and `config/hpv_tracker_config.json`

## Development

### Project Structure

```
hpv-tracker-pro/
├── hpv_tracker_pro.py              # Main application
├── hpv_tracker_pro.spec            # PyInstaller configuration
├── requirements.txt                 # Python dependencies
├── README.md                       # This file
├── README_DEPLOYMENT.md            # Deployment guide
├── LICENSE                         # MIT License
├── data/                           # Database files (gitignored)
│   └── hpv_samples.db             # Main database
├── config/                         # Configuration files (gitignored except examples)
│   ├── hpv_tracker_config.json    # App configuration
│   └── hpv_tracker_config.json.example  # Example config
├── exports/                        # Exported reports (gitignored)
├── backups/                        # Database backups (gitignored)
└── icons/                          # Optional UI icons
```

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

*(Specify your license here - e.g., MIT, GPL, etc.)*

## Version History

- **v1.0** - Initial release with core tracking functionality
  - Sample management with internal references
  - CSV, PDF, and DOCX export
  - Database import/export
  - Audit logging
  - Configuration management

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Acknowledgments

- Built with Python and Tkinter
- PDF generation using ReportLab
- DOCX generation using python-docx
- Image support with Pillow
