"""
Test suite for HPV Tracker Pro
Validates core database operations, imports, exports (CSV, PDF, DOCX),
backups, configuration, and portable standalone app build.
"""

import os
import sys
import unittest
import tempfile
import sqlite3
import csv
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import hpv_tracker_pro as app


class TestHPVTrackerPro(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory and test database for each test."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.test_dir.name)
        self.test_db = str(self.test_path / "test_hpv_samples.db")
        app.init_db(self.test_db)

    def tearDown(self):
        """Clean up temporary directory."""
        self.test_dir.cleanup()

    def test_init_db(self):
        """Verify database tables and indexes are created properly."""
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()

        # Check Sample table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Sample'")
        self.assertIsNotNone(cursor.fetchone())

        # Check AuditLog table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='AuditLog'")
        self.assertIsNotNone(cursor.fetchone())

        conn.close()

    def test_add_and_retrieve_sample(self):
        """Test adding sample and retrieving via all_samples."""
        success, msg, ref = app.add_sample("EP-00101", self.test_db)
        self.assertTrue(success)
        self.assertEqual(ref, 1)

        samples = app.all_samples(self.test_db)
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0][0], 1)
        self.assertEqual(samples[0][1], "EP-00101")

    def test_duplicate_sample(self):
        """Test duplicate episode barcode rejection."""
        app.add_sample("EP-DUP-01", self.test_db)
        success, msg, ref = app.add_sample("EP-DUP-01", self.test_db)
        self.assertFalse(success)
        self.assertIn("already exists", msg)

    def test_empty_sample(self):
        """Test adding empty or whitespace barcode."""
        success, msg, ref = app.add_sample("", self.test_db)
        self.assertFalse(success)
        success, msg, ref = app.add_sample("   ", self.test_db)
        self.assertFalse(success)

    def test_update_sample(self):
        """Test updating an existing sample."""
        _, _, ref = app.add_sample("EP-ORIGINAL", self.test_db)
        success, msg = app.update_sample(ref, "EP-MODIFIED", self.test_db)
        self.assertTrue(success)

        samples = app.all_samples(self.test_db)
        self.assertEqual(samples[0][1], "EP-MODIFIED")

    def test_delete_sample(self):
        """Test deleting a sample."""
        _, _, ref = app.add_sample("EP-TO-DELETE", self.test_db)
        success, msg = app.delete_sample(ref, self.test_db)
        self.assertTrue(success)

        samples = app.all_samples(self.test_db)
        self.assertEqual(len(samples), 0)

    def test_search_samples(self):
        """Test searching samples by query."""
        app.add_sample("EP-SEARCH-ALPHA", self.test_db)
        app.add_sample("EP-SEARCH-BETA", self.test_db)

        results = app.search_samples("ALPHA", self.test_db)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], "EP-SEARCH-ALPHA")

    def test_export_csv(self):
        """Test CSV export functionality."""
        app.add_sample("EP-CSV-1", self.test_db)
        app.add_sample("EP-CSV-2", self.test_db)

        csv_path = str(self.test_path / "export.csv")
        success, msg, count = app.export_csv(csv_path, self.test_db)
        self.assertTrue(success)
        self.assertEqual(count, 2)
        self.assertTrue(os.path.exists(csv_path))

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = list(csv.reader(f))
            self.assertEqual(reader[0], ['InternalRef', 'Episode', 'DateAdded'])
            self.assertEqual(len(reader), 3)

    def test_export_pdf(self):
        """Test PDF report generation."""
        for i in range(1, 10):
            app.add_sample(f"EP-PDF-{i:03d}", self.test_db)

        pdf_path = str(self.test_path / "report.pdf")
        success, msg, count = app.print_pdf(pdf_path, self.test_db)
        self.assertTrue(success)
        self.assertEqual(count, 9)
        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 1000)

    def test_export_docx(self):
        """Test Word document report generation."""
        for i in range(1, 10):
            app.add_sample(f"EP-DOCX-{i:03d}", self.test_db)

        docx_path = str(self.test_path / "report.docx")
        success, msg, count = app.print_docx(docx_path, self.test_db)
        self.assertTrue(success)
        self.assertEqual(count, 9)
        self.assertTrue(os.path.exists(docx_path))
        self.assertGreater(os.path.getsize(docx_path), 1000)

    def test_import_from_csv(self):
        """Test CSV import."""
        import_csv_path = self.test_path / "import_source.csv"
        with open(import_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Episode"])
            writer.writerow(["EP-IMPORTED-1"])
            writer.writerow(["EP-IMPORTED-2"])

        success, msg, count, errors = app.import_from_csv(str(import_csv_path), self.test_db)
        self.assertTrue(success)
        self.assertEqual(count, 2)
        self.assertEqual(len(errors), 0)

        samples = app.all_samples(self.test_db)
        self.assertEqual(len(samples), 2)

    def test_backup_database(self):
        """Test database backup creation."""
        app.add_sample("EP-BACKUP-TEST", self.test_db)
        backup_dest = str(self.test_path / "backup.db")

        success, msg, path = app.backup_data(backup_dest, self.test_db)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(backup_dest))
        self.assertEqual(os.path.getsize(backup_dest), os.path.getsize(self.test_db))

    def test_reset_all_data(self):
        """Test resetting all sample data."""
        app.add_sample("EP-RESET-1", self.test_db)
        app.add_sample("EP-RESET-2", self.test_db)

        success, msg = app.reset_all_data(self.test_db)
        self.assertTrue(success)
        samples = app.all_samples(self.test_db)
        self.assertEqual(len(samples), 0)

    def test_portable_standalone_build(self):
        """Verify the compiled portable standalone app exists and has required components."""
        dist_dir = Path(__file__).parent.resolve() / "dist" / "HPV_Tracker_Pro"
        exe_file = dist_dir / "HPV_Tracker_Pro.exe"
        internal_dir = dist_dir / "_internal"

        self.assertTrue(dist_dir.exists(), "Standalone dist folder must exist")
        self.assertTrue(exe_file.exists(), "HPV_Tracker_Pro.exe must exist in dist folder")
        self.assertGreater(exe_file.stat().st_size, 1000000, "Executable must be valid size (>1MB)")
        self.assertTrue(internal_dir.exists(), "_internal directory must exist")

    def test_windows_compatibility(self):
        """Verify Windows specific components and icon files."""
        ico_file = Path(__file__).parent.resolve() / "icons" / "app_icon.ico"
        self.assertTrue(ico_file.exists(), "Windows icon file must exist")
        self.assertGreater(ico_file.stat().st_size, 1000, "Icon file must be valid size")

        # Test Windows DPI awareness and AppUserModelID calls don't crash
        if sys.platform.startswith('win'):
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('hpv.tracker.pro.test')
            except Exception as e:
                self.fail(f"SetCurrentProcessExplicitAppUserModelID failed: {e}")

    def test_gui_initialization(self):
        """Verify HPVApp GUI initializes without Tcl or Tkinter errors."""
        gui = app.HPVApp()
        gui.update()
        self.assertEqual(gui.title(), "HPV Sample Tracker")
        gui.destroy()


if __name__ == "__main__":
    unittest.main()
