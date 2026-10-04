#!/usr/bin/env python3
"""
HPV Sample Tracker - Desktop application for managing HPV sample records
"""

import json
import os
import sqlite3
import datetime
import getpass
import csv
import subprocess
import sys
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

# Default configuration settings
DEFAULT_CONFIG = {
    'entries_per_page': 90,
    'database_file': 'hpv_samples.db',
    'window_geometry': '900x700',
    'export_directory': str(Path.home()),
    'date_format': '%Y-%m-%d %H:%M:%S',
    'ui_theme': 'clam',
    'backup_directory': str(Path.home() / 'Documents' / 'HPV_Tracker_Backups')
}

CONFIG_FILE = 'hpv_tracker_config.json'

def load_config():
    """
    Load configuration from JSON file with fallback to defaults.
    
    Returns:
        dict: Configuration dictionary with all required settings
    """
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Merge with defaults to ensure all keys exist
            merged_config = DEFAULT_CONFIG.copy()
            merged_config.update(config)
            return merged_config
        else:
            # Return default config if file doesn't exist
            return DEFAULT_CONFIG.copy()
    
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading config file: {e}")
        print("Using default configuration.")
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """
    Save configuration to JSON file.
    
    Args:
        config (dict): Configuration dictionary to save
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    
    except IOError as e:
        print(f"Error saving config file: {e}")
        return False

def get_db(db_file=None):
    """
    Get SQLite database connection with optimizations.
    
    Args:
        db_file (str): Database file path. If None, uses config default.
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    if db_file is None:
        config = load_config()
        db_file = config['database_file']
    
    conn = sqlite3.connect(db_file, timeout=5.0)
    
    # Enable WAL mode for better performance
    conn.execute('PRAGMA journal_mode=WAL')
    
    # Set cache size (10,000 pages)
    conn.execute('PRAGMA cache_size=10000')
    
    # Enable foreign key constraints
    conn.execute('PRAGMA foreign_keys=ON')
    
    return conn

def init_db(db_file=None):
    """
    Initialize database with required tables and indexes.
    
    Args:
        db_file (str): Database file path. If None, uses config default.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db(db_file)
        cursor = conn.cursor()
        
        # Create Sample table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Sample (
                InternalRef INTEGER PRIMARY KEY AUTOINCREMENT,
                Episode TEXT UNIQUE NOT NULL,
                DateAdded TEXT DEFAULT (datetime('now'))
            )
        ''')
        
        # Create AuditLog table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS AuditLog (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                WhenUtc TEXT NOT NULL,
                UserName TEXT NOT NULL,
                Action TEXT NOT NULL,
                Details TEXT
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sample_episode ON Sample(Episode)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_when ON AuditLog(WhenUtc)')
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
        return False

def log_audit(action, details=None, db_file=None):
    """
    Log an audit entry.
    
    Args:
        action (str): Action performed
        details (str): Additional details about the action
        db_file (str): Database file path. If None, uses config default.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db(db_file)
        cursor = conn.cursor()
        
        username = getpass.getuser()
        when_utc = datetime.datetime.utcnow().isoformat()
        
        cursor.execute('''
            INSERT INTO AuditLog (WhenUtc, UserName, Action, Details)
            VALUES (?, ?, ?, ?)
        ''', (when_utc, username, action, details))
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"Audit logging error: {e}")
        return False

def add_sample(episode, db_file=None):
    """
    Add a new sample with unique episode check and audit logging.
    
    Args:
        episode (str): Episode barcode
        db_file (str): Database file path. If None, uses config default.
    
    Returns:
        tuple: (success: bool, message: str, internal_ref: int or None)
    """
    if not episode or not episode.strip():
        return False, "Episode barcode cannot be empty", None
    
    episode = episode.strip()
    
    try:
        conn = get_db(db_file)
        cursor = conn.cursor()
        
        # Check for duplicate episode
        cursor.execute('SELECT InternalRef FROM Sample WHERE Episode = ?', (episode,))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return False, f"Episode '{episode}' already exists with InternalRef {existing[0]}", None
        
        # Insert new sample
        cursor.execute('INSERT INTO Sample (Episode) VALUES (?)', (episode,))
        internal_ref = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        # Log audit
        log_audit("INSERT", f"Added sample: Episode={episode}, InternalRef={internal_ref}", db_file)
        
        return True, f"Sample added successfully with InternalRef {internal_ref}", internal_ref
        
    except sqlite3.Error as e:
        return False, f"Database error: {e}", None

def all_samples(db_file=None):
    """
    Retrieve all samples sorted by InternalRef.
    
    Args:
        db_file (str): Database file path. If None, uses config default.
    
    Returns:
        list: List of tuples (InternalRef, Episode, DateAdded)
    """
    try:
        conn = get_db(db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT InternalRef, Episode, DateAdded FROM Sample ORDER BY InternalRef')
        samples = cursor.fetchall()
        
        conn.close()
        return samples
        
    except sqlite3.Error as e:
        print(f"Error retrieving samples: {e}")
        return []

def delete_sample(internal_ref, db_file=None):
    """
    Delete a sample with audit logging.
    
    Args:
        internal_ref (int): Internal reference number
        db_file (str): Database file path. If None, uses config default.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        conn = get_db(db_file)
        cursor = conn.cursor()
        
        # Get sample details before deletion
        cursor.execute('SELECT Episode FROM Sample WHERE InternalRef = ?', (internal_ref,))
        sample = cursor.fetchone()
        
        if not sample:
            conn.close()
            return False, f"Sample with InternalRef {internal_ref} not found"
        
        episode = sample[0]
        
        # Delete sample
        cursor.execute('DELETE FROM Sample WHERE InternalRef = ?', (internal_ref,))
        
        if cursor.rowcount == 0:
            conn.close()
            return False, f"Sample with InternalRef {internal_ref} not found"
        
        conn.commit()
        conn.close()
        
        # Log audit
        log_audit("DELETE", f"Deleted sample: Episode={episode}, InternalRef={internal_ref}", db_file)
        
        return True, f"Sample {internal_ref} deleted successfully"
        
    except sqlite3.Error as e:
        return False, f"Database error: {e}"

def update_sample(internal_ref, new_episode, db_file=None):
    """
    Update a sample with duplicate check and audit logging.
    
    Args:
        internal_ref (int): Internal reference number
        new_episode (str): New episode barcode
        db_file (str): Database file path. If None, uses config default.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if not new_episode or not new_episode.strip():
        return False, "Episode barcode cannot be empty"
    
    new_episode = new_episode.strip()
    
    try:
        conn = get_db(db_file)
        cursor = conn.cursor()
        
        # Get current episode
        cursor.execute('SELECT Episode FROM Sample WHERE InternalRef = ?', (internal_ref,))
        current = cursor.fetchone()
        
        if not current:
            conn.close()
            return False, f"Sample with InternalRef {internal_ref} not found"
        
        old_episode = current[0]
        
        # If episode hasn't changed, no update needed
        if old_episode == new_episode:
            conn.close()
            return True, "No changes made"
        
        # Check for duplicate episode (excluding current sample)
        cursor.execute('SELECT InternalRef FROM Sample WHERE Episode = ? AND InternalRef != ?', 
                      (new_episode, internal_ref))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return False, f"Episode '{new_episode}' already exists with InternalRef {existing[0]}"
        
        # Update sample
        cursor.execute('UPDATE Sample SET Episode = ? WHERE InternalRef = ?', 
                      (new_episode, internal_ref))
        
        conn.commit()
        conn.close()
        
        # Log audit
        log_audit("UPDATE", f"Updated sample {internal_ref}: Episode changed from '{old_episode}' to '{new_episode}'", db_file)
        
        return True, f"Sample {internal_ref} updated successfully"
        
    except sqlite3.Error as e:
        return False, f"Database error: {e}"

def reset_all_data(db_file=None):
    """
    Reset all sample data with audit logging.
    
    Args:
        db_file (str): Database file path. If None, uses config default.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        conn = get_db(db_file)
        cursor = conn.cursor()
        
        # Count samples before deletion
        cursor.execute('SELECT COUNT(*) FROM Sample')
        count = cursor.fetchone()[0]
        
        # Delete all samples
        cursor.execute('DELETE FROM Sample')
        
        # Reset auto-increment counter
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="Sample"')
        
        conn.commit()
        conn.close()
        
        # Log audit
        log_audit("RESET", f"Reset all data: {count} samples deleted", db_file)
        
        return True, f"All data reset successfully. {count} samples deleted."
        
    except sqlite3.Error as e:
        return False, f"Database error: {e}"

def import_from_csv(csv_file, db_file=None):
    """
    Import sample data from CSV file with header detection, error reporting, and audit logging.
    
    Args:
        csv_file (str): Path to CSV file
        db_file (str): Database file path. If None, uses config default.
    
    Returns:
        tuple: (success: bool, message: str, imported_count: int, errors: list)
    """
    if not os.path.exists(csv_file):
        return False, f"CSV file '{csv_file}' not found", 0, []
    
    imported_count = 0
    errors = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            # Detect if file has headers
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            has_header = sniffer.has_header(sample)
            
            reader = csv.reader(f)
            
            # Skip header if present
            if has_header:
                next(reader)
            
            conn = get_db(db_file)
            cursor = conn.cursor()
            
            for row_num, row in enumerate(reader, start=2 if has_header else 1):
                if not row or len(row) == 0:
                    continue
                
                # Get episode from first column
                episode = str(row[0]).strip() if row[0] else ""
                
                if not episode:
                    errors.append(f"Row {row_num}: Empty episode barcode")
                    continue
                
                try:
                    # Check for duplicate episode
                    cursor.execute('SELECT InternalRef FROM Sample WHERE Episode = ?', (episode,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        errors.append(f"Row {row_num}: Episode '{episode}' already exists with InternalRef {existing[0]}")
                        continue
                    
                    # Insert new sample
                    cursor.execute('INSERT INTO Sample (Episode) VALUES (?)', (episode,))
                    imported_count += 1
                    
                except sqlite3.Error as e:
                    errors.append(f"Row {row_num}: Database error - {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            # Log audit
            log_audit("IMPORT_CSV", f"Imported {imported_count} samples from {csv_file}. {len(errors)} errors.", db_file)
            
            if imported_count > 0:
                message = f"Successfully imported {imported_count} samples"
                if errors:
                    message += f" with {len(errors)} errors"
                return True, message, imported_count, errors
            else:
                return False, "No samples were imported", 0, errors
                
    except (IOError, csv.Error) as e:
        return False, f"Error reading CSV file: {e}", 0, []

def import_from_database(source_db_file, target_db_file=None):
    """
    Import sample data from SQLite database with error handling.
    
    Args:
        source_db_file (str): Path to source database file
        target_db_file (str): Target database file path. If None, uses config default.
    
    Returns:
        tuple: (success: bool, message: str, imported_count: int, errors: list)
    """
    if not os.path.exists(source_db_file):
        return False, f"Source database '{source_db_file}' not found", 0, []
    
    imported_count = 0
    errors = []
    
    try:
        # Connect to source database
        source_conn = sqlite3.connect(source_db_file, timeout=5.0)
        source_cursor = source_conn.cursor()
        
        # Check if Sample table exists in source
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Sample'")
        if not source_cursor.fetchone():
            source_conn.close()
            return False, "Source database does not contain a 'Sample' table", 0, []
        
        # Get all samples from source
        source_cursor.execute('SELECT Episode FROM Sample ORDER BY InternalRef')
        source_samples = source_cursor.fetchall()
        source_conn.close()
        
        if not source_samples:
            return False, "No samples found in source database", 0, []
        
        # Connect to target database
        target_conn = get_db(target_db_file)
        target_cursor = target_conn.cursor()
        
        for episode_tuple in source_samples:
            episode = episode_tuple[0].strip() if episode_tuple[0] else ""
            
            if not episode:
                errors.append(f"Empty episode barcode found")
                continue
            
            try:
                # Check for duplicate episode
                target_cursor.execute('SELECT InternalRef FROM Sample WHERE Episode = ?', (episode,))
                existing = target_cursor.fetchone()
                
                if existing:
                    errors.append(f"Episode '{episode}' already exists with InternalRef {existing[0]}")
                    continue
                
                # Insert new sample
                target_cursor.execute('INSERT INTO Sample (Episode) VALUES (?)', (episode,))
                imported_count += 1
                
            except sqlite3.Error as e:
                errors.append(f"Episode '{episode}': Database error - {e}")
                continue
        
        target_conn.commit()
        target_conn.close()
        
        # Log audit
        log_audit("IMPORT_DB", f"Imported {imported_count} samples from {source_db_file}. {len(errors)} errors.", target_db_file)
        
        if imported_count > 0:
            message = f"Successfully imported {imported_count} samples"
            if errors:
                message += f" with {len(errors)} errors"
            return True, message, imported_count, errors
        else:
            return False, "No samples were imported", 0, errors
            
    except sqlite3.Error as e:
        return False, f"Database error: {e}", 0, []

def export_csv(csv_file, db_file=None):
    """
    Export sample data to CSV file with progress tracking.
    
    Args:
        csv_file (str): Path to output CSV file
        db_file (str): Database file path. If None, uses config default.
    
    Returns:
        tuple: (success: bool, message: str, exported_count: int)
    """
    try:
        samples = all_samples(db_file)
        
        if not samples:
            return False, "No samples to export", 0
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['InternalRef', 'Episode', 'DateAdded'])
            
            # Write data
            for sample in samples:
                writer.writerow(sample)
        
        # Log audit
        log_audit("EXPORT_CSV", f"Exported {len(samples)} samples to {csv_file}", db_file)
        
        return True, f"Successfully exported {len(samples)} samples to CSV", len(samples)
        
    except IOError as e:
        return False, f"Error writing CSV file: {e}", 0

def print_pdf(pdf_file, db_file=None):
    """
    Export sample data to PDF file with fixed layout (90 entries/page), progress bar, and file opening.
    
    Args:
        pdf_file (str): Path to output PDF file
        db_file (str): Database file path. If None, uses config default.
    
    Returns:
        tuple: (success: bool, message: str, exported_count: int)
    """
    try:
        # Lazy import of ReportLab
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
    except ImportError:
        return False, "ReportLab library not found. Please install with: pip install reportlab", 0
    
    try:
        config = load_config()
        samples = all_samples(db_file)
        
        if not samples:
            return False, "No samples to export", 0
        
        # Get padded data for consistent layout
        entries_per_page = config.get('entries_per_page', 90)
        padded_samples = _get_padded_data(samples, entries_per_page)
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_file, pagesize=A4, 
                               rightMargin=0.5*inch, leftMargin=0.5*inch,
                               topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Create styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        # Build document content
        story = []
        
        # Add title
        title = Paragraph("HPV Sample Tracker - Sample Report", title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Add generation info
        generation_info = Paragraph(
            f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            f"Total samples: {len(samples)}<br/>"
            f"Report format: {entries_per_page} entries per page (3 trays of 30)",
            styles['Normal']
        )
        story.append(generation_info)
        story.append(Spacer(1, 20))
        
        # Process samples in pages
        page_count = 0
        for page_start in range(0, len(padded_samples), entries_per_page):
            page_count += 1
            page_samples = padded_samples[page_start:page_start + entries_per_page]
            
            # Add page header
            page_header = Paragraph(f"Page {page_count}", styles['Heading2'])
            story.append(page_header)
            story.append(Spacer(1, 12))
            
            # Create table data for this page (3 trays of 30 entries each)
            table_data = []
            
            # Process in groups of 30 (trays)
            for tray_num in range(3):
                tray_start = tray_num * 30
                tray_end = min(tray_start + 30, len(page_samples))
                tray_samples = page_samples[tray_start:tray_end]
                
                # Add tray header
                table_data.append([f"Tray {tray_num + 1}", "", ""])
                table_data.append(["Internal Ref", "Episode", "Date Added"])
                
                # Add tray samples
                for sample in tray_samples:
                    internal_ref = str(sample[0]) if sample[0] else ""
                    episode = str(sample[1]) if sample[1] else ""
                    date_added = str(sample[2]) if sample[2] else ""
                    table_data.append([internal_ref, episode, date_added])
                
                # Add spacing between trays
                if tray_num < 2:
                    table_data.append(["", "", ""])
            
            # Create table
            table = Table(table_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch])
            
            # Apply table style
            table.setStyle(TableStyle([
                # Header styles
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                
                # Data styles
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                
                # Tray header styles
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('BACKGROUND', (0, 32), (-1, 32), colors.lightgrey),
                ('BACKGROUND', (0, 64), (-1, 64), colors.lightgrey),
                
                # Column header styles  
                ('BACKGROUND', (0, 1), (-1, 1), colors.lightblue),
                ('BACKGROUND', (0, 33), (-1, 33), colors.lightblue),
                ('BACKGROUND', (0, 65), (-1, 65), colors.lightblue),
            ]))
            
            story.append(table)
            
            # Add page break if not last page
            if page_start + entries_per_page < len(padded_samples):
                story.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(story)
        
        # Log audit
        log_audit("EXPORT_PDF", f"Exported {len(samples)} samples to {pdf_file}", db_file)
        
        return True, f"Successfully exported {len(samples)} samples to PDF ({page_count} pages)", len(samples)
        
    except Exception as e:
        return False, f"Error creating PDF file: {e}", 0

def print_docx(docx_file, db_file=None):
    """
    Export sample data to DOCX file with similar layout, progress bar, and file opening.
    
    Args:
        docx_file (str): Path to output DOCX file
        db_file (str): Database file path. If None, uses config default.
    
    Returns:
        tuple: (success: bool, message: str, exported_count: int)
    """
    try:
        # Lazy import of python-docx
        from docx import Document
        from docx.shared import Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.shared import OxmlElement, qn
        
    except ImportError:
        return False, "python-docx library not found. Please install with: pip install python-docx", 0
    
    try:
        config = load_config()
        samples = all_samples(db_file)
        
        if not samples:
            return False, "No samples to export", 0
        
        # Get padded data for consistent layout
        entries_per_page = config.get('entries_per_page', 90)
        padded_samples = _get_padded_data(samples, entries_per_page)
        
        # Create document
        doc = Document()
        
        # Add title
        title = doc.add_heading('HPV Sample Tracker - Sample Report', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add generation info
        info_para = doc.add_paragraph()
        info_para.add_run(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        info_para.add_run(f"Total samples: {len(samples)}\n")
        info_para.add_run(f"Report format: {entries_per_page} entries per page (3 trays of 30)")
        
        # Process samples in pages
        page_count = 0
        for page_start in range(0, len(padded_samples), entries_per_page):
            page_count += 1
            page_samples = padded_samples[page_start:page_start + entries_per_page]
            
            # Add page header
            doc.add_heading(f'Page {page_count}', level=1)
            
            # Process in groups of 30 (trays)
            for tray_num in range(3):
                tray_start = tray_num * 30
                tray_end = min(tray_start + 30, len(page_samples))
                tray_samples = page_samples[tray_start:tray_end]
                
                # Add tray header
                tray_header = doc.add_heading(f'Tray {tray_num + 1}', level=2)
                
                # Create table for this tray
                table = doc.add_table(rows=1, cols=3)
                table.style = 'Table Grid'
                
                # Add header row
                hdr_cells = table.rows[0].cells
                hdr_cells[0].text = 'Internal Ref'
                hdr_cells[1].text = 'Episode'
                hdr_cells[2].text = 'Date Added'
                
                # Make header bold
                for cell in hdr_cells:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.bold = True
                
                # Add data rows
                for sample in tray_samples:
                    row_cells = table.add_row().cells
                    row_cells[0].text = str(sample[0]) if sample[0] else ""
                    row_cells[1].text = str(sample[1]) if sample[1] else ""
                    row_cells[2].text = str(sample[2]) if sample[2] else ""
                
                # Add spacing between trays
                if tray_num < 2:
                    doc.add_paragraph()
            
            # Add page break if not last page
            if page_start + entries_per_page < len(padded_samples):
                doc.add_page_break()
        
        # Save document
        doc.save(docx_file)
        
        # Log audit
        log_audit("EXPORT_DOCX", f"Exported {len(samples)} samples to {docx_file}", db_file)
        
        return True, f"Successfully exported {len(samples)} samples to DOCX ({page_count} pages)", len(samples)
        
    except Exception as e:
        return False, f"Error creating DOCX file: {e}", 0

def _get_padded_data(samples, entries_per_page=90):
    """
    Get sample data padded to fill complete pages for consistent export formatting.
    
    Args:
        samples (list): List of sample tuples
        entries_per_page (int): Number of entries per page
    
    Returns:
        list: Padded list of samples
    """
    if not samples:
        return []
    
    # Calculate how many entries needed to fill complete pages
    total_entries = len(samples)
    pages_needed = (total_entries + entries_per_page - 1) // entries_per_page
    padded_total = pages_needed * entries_per_page
    
    # Create padded list
    padded_samples = list(samples)
    
    # Add empty entries to fill complete pages
    for i in range(padded_total - total_entries):
        padded_samples.append(("", "", ""))
    
    return padded_samples

def backup_data(backup_file=None, db_file=None):
    """
    Create a backup of the database with timestamped filename.
    
    Args:
        backup_file (str): Path to backup file. If None, uses config backup directory with timestamp.
        db_file (str): Database file path. If None, uses config default.
    
    Returns:
        tuple: (success: bool, message: str, backup_path: str or None)
    """
    try:
        config = load_config()
        
        # Get source database file
        if db_file is None:
            db_file = config['database_file']
        
        if not os.path.exists(db_file):
            return False, f"Database file '{db_file}' not found", None
        
        # Generate backup filename if not provided
        if backup_file is None:
            backup_dir = Path(config['backup_directory'])
            
            # Create backup directory if it doesn't exist
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamped filename
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"hpv_samples_backup_{timestamp}.db"
            backup_file = backup_dir / backup_filename
        
        # Copy database file to backup location
        shutil.copy2(db_file, backup_file)
        
        # Verify backup was created successfully
        if os.path.exists(backup_file):
            backup_size = os.path.getsize(backup_file)
            original_size = os.path.getsize(db_file)
            
            if backup_size == original_size:
                # Log audit
                log_audit("BACKUP", f"Database backed up to {backup_file}", db_file)
                
                return True, f"Database successfully backed up to {backup_file}", str(backup_file)
            else:
                return False, "Backup file size mismatch - backup may be corrupted", None
        else:
            return False, "Backup file was not created", None
            
    except (IOError, OSError) as e:
        return False, f"Error creating backup: {e}", None

def load_icon(icon_name):
    """
    Load an icon from the icons directory.
    
    Args:
        icon_name (str): Name of the icon file (without extension)
    
    Returns:
        PhotoImage or None: Loaded icon or None if not found/error
    """
    try:
        # Try to import PIL for better image support
        from PIL import Image, ImageTk
        
        icon_path = Path("icons") / f"{icon_name}.png"
        
        if icon_path.exists():
            # Load with PIL for better compatibility
            image = Image.open(icon_path)
            # Resize to 16x16 if needed
            if image.size != (16, 16):
                image = image.resize((16, 16), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(image)
        
    except ImportError:
        # Fall back to tkinter PhotoImage if PIL not available
        try:
            icon_path = Path("icons") / f"{icon_name}.png"
            if icon_path.exists():
                return tk.PhotoImage(file=str(icon_path))
        except tk.TclError:
            pass
    
    except Exception:
        pass
    
    return None

class HPVApp(tk.Tk):
    """
    Main application class for HPV Sample Tracker.
    """
    
    def __init__(self):
        super().__init__()
        
        # Load configuration
        self.app_config = load_config()
        
        # Initialize database
        init_db()
        
        # Load icons first
        self.load_icons()
        
        # Set up the main window
        self.setup_window()
        
        # Create GUI components
        self.create_widgets()
        
        # Load initial data
        self.refresh_samples()
        
        # Set up event bindings
        self.setup_bindings()
    
    def load_icons(self):
        """Load icons from the icons directory."""
        self.icons = {}
        
        # Define icon mappings
        icon_names = [
            'add', 'edit', 'delete', 'search', 'export', 'import', 
            'backup', 'reset', 'csv', 'pdf', 'docx', 'database'
        ]
        
        # Load each icon
        for icon_name in icon_names:
            icon = load_icon(icon_name)
            if icon:
                self.icons[icon_name] = icon
    
    def create_button_with_icon(self, parent, text, command, icon_name=None):
        """Create a button with optional icon."""
        if icon_name and icon_name in self.icons:
            return ttk.Button(parent, text=text, command=command, image=self.icons[icon_name], compound=tk.LEFT)
        else:
            return ttk.Button(parent, text=text, command=command)
    
    def setup_window(self):
        """Set up the main window properties."""
        self.title("HPV Sample Tracker")
        self.geometry(self.app_config['window_geometry'])
        
        # Apply theme
        style = ttk.Style()
        style.theme_use(self.app_config['ui_theme'])
        
        # Configure colors
        style.configure('TButton', background='#4a6baf')
        self.configure(bg='#f0f0f0')
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """Create and layout all GUI widgets."""
        # Create menu bar
        self.create_menu_bar()
        
        # Main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top controls frame
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Starting internal reference controls
        ttk.Label(top_frame, text="Starting Internal Ref:").pack(side=tk.LEFT)
        self.start_ref_var = tk.StringVar()
        self.start_ref_entry = ttk.Entry(top_frame, textvariable=self.start_ref_var, width=10)
        self.start_ref_entry.pack(side=tk.LEFT, padx=(5, 10))
        ttk.Button(top_frame, text="Set", command=self.set_starting_ref).pack(side=tk.LEFT)
        
        # Input section frame
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(input_frame, text="Episode Barcode:").pack(side=tk.LEFT)
        self.episode_var = tk.StringVar()
        self.episode_entry = ttk.Entry(input_frame, textvariable=self.episode_var, width=20)
        self.episode_entry.pack(side=tk.LEFT, padx=(5, 10))
        ttk.Button(input_frame, text="Add Sample", command=self.add_sample_gui).pack(side=tk.LEFT)
        
        # Search section frame
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # Table frame
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create treeview
        columns = ('InternalRef', 'Episode', 'DateAdded')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Define column headings and widths
        self.tree.heading('InternalRef', text='Internal Ref')
        self.tree.heading('Episode', text='Episode')
        self.tree.heading('DateAdded', text='Date Added')
        
        self.tree.column('InternalRef', width=100, anchor=tk.CENTER)
        self.tree.column('Episode', width=200, anchor=tk.W)
        self.tree.column('DateAdded', width=150, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button bar frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create buttons with optional icons
        self.create_button_with_icon(button_frame, "Export CSV", self.export_csv_gui, "csv").pack(side=tk.LEFT, padx=(0, 5))
        self.create_button_with_icon(button_frame, "Export PDF", self.export_pdf_gui, "pdf").pack(side=tk.LEFT, padx=(0, 5))
        self.create_button_with_icon(button_frame, "Export DOCX", self.export_docx_gui, "docx").pack(side=tk.LEFT, padx=(0, 5))
        self.create_button_with_icon(button_frame, "Import CSV", self.import_csv_gui, "import").pack(side=tk.LEFT, padx=(0, 5))
        self.create_button_with_icon(button_frame, "Import Database", self.import_db_gui, "database").pack(side=tk.LEFT, padx=(0, 5))
        self.create_button_with_icon(button_frame, "Delete Selected", self.delete_selected, "delete").pack(side=tk.LEFT, padx=(0, 5))
        self.create_button_with_icon(button_frame, "Backup Data", self.backup_data_gui, "backup").pack(side=tk.LEFT, padx=(0, 5))
        self.create_button_with_icon(button_frame, "Reset All Data", self.reset_all_data_gui, "reset").pack(side=tk.LEFT, padx=(0, 5))
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Progress bar (initially hidden)
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
    
    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import CSV...", command=self.import_csv_gui)
        file_menu.add_command(label="Export CSV...", command=self.export_csv_gui)
        file_menu.add_command(label="Export PDF...", command=self.export_pdf_gui)
        file_menu.add_command(label="Export DOCX...", command=self.export_docx_gui)
        file_menu.add_separator()
        file_menu.add_command(label="Backup...", command=self.backup_data_gui)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Edit Sample", command=self.edit_selected)
        edit_menu.add_command(label="Delete Sample", command=self.delete_selected)
        edit_menu.add_separator()
        edit_menu.add_command(label="Reset All Data", command=self.reset_all_data_gui)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def setup_bindings(self):
        """Set up keyboard and event bindings."""
        # Enter key to add sample
        self.episode_entry.bind('<Return>', lambda e: self.add_sample_gui())
        
        # Delete key to delete selected
        self.tree.bind('<Delete>', lambda e: self.delete_selected())
        
        # Double-click to edit
        self.tree.bind('<Double-1>', lambda e: self.edit_selected())
        
        # Search on key release
        self.search_var.trace('w', self.filter_samples)
    
    def refresh_samples(self):
        """Refresh the samples display."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get all samples
        samples = all_samples()
        
        # Add samples to tree
        for sample in samples:
            self.tree.insert('', tk.END, values=sample)
        
        # Update status
        self.status_var.set(f"Loaded {len(samples)} samples")
    
    def filter_samples(self, *args):
        """Filter samples based on search text."""
        search_text = self.search_var.get().lower()
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get all samples
        samples = all_samples()
        
        # Filter and add samples
        filtered_count = 0
        for sample in samples:
            # Search in InternalRef, Episode, and DateAdded
            if (search_text in str(sample[0]).lower() or 
                search_text in str(sample[1]).lower() or 
                search_text in str(sample[2]).lower()):
                self.tree.insert('', tk.END, values=sample)
                filtered_count += 1
        
        # Update status
        if search_text:
            self.status_var.set(f"Showing {filtered_count} of {len(samples)} samples")
        else:
            self.status_var.set(f"Loaded {len(samples)} samples")
    
    def add_sample_gui(self):
        """Add a sample from GUI input."""
        episode = self.episode_var.get().strip()
        
        if not episode:
            messagebox.showerror("Error", "Please enter an episode barcode")
            return
        
        success, message, internal_ref = add_sample(episode)
        
        if success:
            self.episode_var.set("")  # Clear input
            self.refresh_samples()
            self.status_var.set(message)
        else:
            messagebox.showerror("Error", message)
    
    def delete_selected(self):
        """Delete selected samples."""
        selected_items = self.tree.selection()
        
        if not selected_items:
            messagebox.showwarning("Warning", "Please select samples to delete")
            return
        
        # Confirm deletion
        count = len(selected_items)
        if not messagebox.askyesno("Confirm Delete", 
                                  f"Are you sure you want to delete {count} sample(s)?"):
            return
        
        deleted_count = 0
        errors = []
        
        for item in selected_items:
            values = self.tree.item(item, 'values')
            internal_ref = int(values[0])
            
            success, message = delete_sample(internal_ref)
            if success:
                deleted_count += 1
            else:
                errors.append(f"InternalRef {internal_ref}: {message}")
        
        # Refresh display
        self.refresh_samples()
        
        # Show results
        if deleted_count > 0:
            self.status_var.set(f"Deleted {deleted_count} samples")
            if errors:
                messagebox.showwarning("Partial Success", 
                                     f"Deleted {deleted_count} samples, but {len(errors)} errors occurred:\n" + 
                                     "\n".join(errors[:5]))  # Show first 5 errors
        else:
            messagebox.showerror("Error", "No samples were deleted:\n" + "\n".join(errors[:5]))
    
    def edit_selected(self):
        """Edit selected sample."""
        selected_items = self.tree.selection()
        
        if not selected_items:
            messagebox.showwarning("Warning", "Please select a sample to edit")
            return
        
        if len(selected_items) > 1:
            messagebox.showwarning("Warning", "Please select only one sample to edit")
            return
        
        # Get selected sample data
        item = selected_items[0]
        values = self.tree.item(item, 'values')
        internal_ref = int(values[0])
        current_episode = values[1]
        
        # Show edit dialog
        self.show_edit_dialog(internal_ref, current_episode)
    
    def show_edit_dialog(self, internal_ref, current_episode):
        """Show edit dialog for a sample."""
        dialog = tk.Toplevel(self)
        dialog.title("Edit Sample")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.winfo_rootx() + 50, self.winfo_rooty() + 50))
        
        # Create dialog content
        ttk.Label(dialog, text=f"Internal Ref: {internal_ref}").pack(pady=10)
        
        ttk.Label(dialog, text="Episode:").pack()
        episode_var = tk.StringVar(value=current_episode)
        episode_entry = ttk.Entry(dialog, textvariable=episode_var, width=30)
        episode_entry.pack(pady=5)
        episode_entry.focus()
        episode_entry.select_range(0, tk.END)
        
        # Button frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        def save_changes():
            new_episode = episode_var.get().strip()
            if not new_episode:
                messagebox.showerror("Error", "Episode cannot be empty")
                return
            
            success, message = update_sample(internal_ref, new_episode)
            if success:
                dialog.destroy()
                self.refresh_samples()
                self.status_var.set(message)
            else:
                messagebox.showerror("Error", message)
        
        def cancel_edit():
            dialog.destroy()
        
        ttk.Button(button_frame, text="Save", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel_edit).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key to save
        episode_entry.bind('<Return>', lambda e: save_changes())
        dialog.bind('<Escape>', lambda e: cancel_edit())
    
    def import_csv_gui(self):
        """Import samples from CSV file."""
        filename = filedialog.askopenfilename(
            title="Import CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        # Show progress
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.start()
        self.status_var.set("Importing CSV...")
        self.update()
        
        try:
            success, message, count, errors = import_from_csv(filename)
            
            # Hide progress
            self.progress.stop()
            self.progress.pack_forget()
            
            if success:
                self.refresh_samples()
                self.status_var.set(message)
                
                if errors:
                    # Show errors in a separate dialog
                    error_dialog = tk.Toplevel(self)
                    error_dialog.title("Import Errors")
                    error_dialog.geometry("600x400")
                    
                    ttk.Label(error_dialog, text=f"Import completed with {len(errors)} errors:").pack(pady=10)
                    
                    # Create text widget with scrollbar
                    text_frame = ttk.Frame(error_dialog)
                    text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                    
                    text_widget = tk.Text(text_frame, wrap=tk.WORD)
                    scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
                    text_widget.configure(yscrollcommand=scrollbar.set)
                    
                    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                    
                    # Insert errors
                    for error in errors:
                        text_widget.insert(tk.END, error + "\n")
                    
                    text_widget.config(state=tk.DISABLED)
                    
                    ttk.Button(error_dialog, text="Close", command=error_dialog.destroy).pack(pady=10)
            else:
                self.status_var.set("Import failed")
                messagebox.showerror("Import Error", message)
                
        except Exception as e:
            self.progress.stop()
            self.progress.pack_forget()
            self.status_var.set("Import failed")
            messagebox.showerror("Import Error", f"Unexpected error: {e}")
    
    def import_db_gui(self):
        """Import samples from database file."""
        filename = filedialog.askopenfilename(
            title="Import Database File",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        # Show progress
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.start()
        self.status_var.set("Importing database...")
        self.update()
        
        try:
            success, message, count, errors = import_from_database(filename)
            
            # Hide progress
            self.progress.stop()
            self.progress.pack_forget()
            
            if success:
                self.refresh_samples()
                self.status_var.set(message)
                
                if errors:
                    messagebox.showwarning("Import Warning", 
                                         f"Import completed with {len(errors)} errors. Check the log for details.")
            else:
                self.status_var.set("Import failed")
                messagebox.showerror("Import Error", message)
                
        except Exception as e:
            self.progress.stop()
            self.progress.pack_forget()
            self.status_var.set("Import failed")
            messagebox.showerror("Import Error", f"Unexpected error: {e}")
    
    def export_csv_gui(self):
        """Export samples to CSV file."""
        filename = filedialog.asksaveasfilename(
            title="Export CSV File",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        # Show progress
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.start()
        self.status_var.set("Exporting CSV...")
        self.update()
        
        try:
            success, message, count = export_csv(filename)
            
            # Hide progress
            self.progress.stop()
            self.progress.pack_forget()
            
            if success:
                self.status_var.set(message)
                
                # Ask if user wants to open the file
                if messagebox.askyesno("Export Complete", f"{message}\n\nWould you like to open the file?"):
                    try:
                        if sys.platform.startswith('win'):
                            os.startfile(filename)
                        elif sys.platform.startswith('darwin'):
                            subprocess.call(['open', filename])
                        else:
                            subprocess.call(['xdg-open', filename])
                    except Exception as e:
                        messagebox.showwarning("Warning", f"Could not open file: {e}")
            else:
                self.status_var.set("Export failed")
                messagebox.showerror("Export Error", message)
                
        except Exception as e:
            self.progress.stop()
            self.progress.pack_forget()
            self.status_var.set("Export failed")
            messagebox.showerror("Export Error", f"Unexpected error: {e}")
    
    def export_pdf_gui(self):
        """Export samples to PDF file."""
        filename = filedialog.asksaveasfilename(
            title="Export PDF File",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        # Show progress
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.start()
        self.status_var.set("Exporting PDF...")
        self.update()
        
        try:
            success, message, count = print_pdf(filename)
            
            # Hide progress
            self.progress.stop()
            self.progress.pack_forget()
            
            if success:
                self.status_var.set(message)
                
                # Ask if user wants to open the file
                if messagebox.askyesno("Export Complete", f"{message}\n\nWould you like to open the file?"):
                    try:
                        if sys.platform.startswith('win'):
                            os.startfile(filename)
                        elif sys.platform.startswith('darwin'):
                            subprocess.call(['open', filename])
                        else:
                            subprocess.call(['xdg-open', filename])
                    except Exception as e:
                        messagebox.showwarning("Warning", f"Could not open file: {e}")
            else:
                self.status_var.set("Export failed")
                messagebox.showerror("Export Error", message)
                
        except Exception as e:
            self.progress.stop()
            self.progress.pack_forget()
            self.status_var.set("Export failed")
            messagebox.showerror("Export Error", f"Unexpected error: {e}")
    
    def export_docx_gui(self):
        """Export samples to DOCX file."""
        filename = filedialog.asksaveasfilename(
            title="Export DOCX File",
            defaultextension=".docx",
            filetypes=[("Word documents", "*.docx"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        # Show progress
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.start()
        self.status_var.set("Exporting DOCX...")
        self.update()
        
        try:
            success, message, count = print_docx(filename)
            
            # Hide progress
            self.progress.stop()
            self.progress.pack_forget()
            
            if success:
                self.status_var.set(message)
                
                # Ask if user wants to open the file
                if messagebox.askyesno("Export Complete", f"{message}\n\nWould you like to open the file?"):
                    try:
                        if sys.platform.startswith('win'):
                            os.startfile(filename)
                        elif sys.platform.startswith('darwin'):
                            subprocess.call(['open', filename])
                        else:
                            subprocess.call(['xdg-open', filename])
                    except Exception as e:
                        messagebox.showwarning("Warning", f"Could not open file: {e}")
            else:
                self.status_var.set("Export failed")
                messagebox.showerror("Export Error", message)
                
        except Exception as e:
            self.progress.stop()
            self.progress.pack_forget()
            self.status_var.set("Export failed")
            messagebox.showerror("Export Error", f"Unexpected error: {e}")
    
    def backup_data_gui(self):
        """Create a backup of the database."""
        filename = filedialog.asksaveasfilename(
            title="Backup Database",
            defaultextension=".db",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        success, message, backup_path = backup_data(filename)
        
        if success:
            self.status_var.set("Backup created successfully")
            messagebox.showinfo("Backup Complete", message)
        else:
            messagebox.showerror("Backup Error", message)
    
    def reset_all_data_gui(self):
        """Reset all sample data with confirmation."""
        if not messagebox.askyesno("Confirm Reset", 
                                  "Are you sure you want to delete ALL samples?\n\n" +
                                  "This action cannot be undone!"):
            return
        
        # Double confirmation
        if not messagebox.askyesno("Final Confirmation", 
                                  "This will permanently delete all samples.\n\n" +
                                  "Are you absolutely sure?"):
            return
        
        success, message = reset_all_data()
        
        if success:
            self.refresh_samples()
            self.status_var.set(message)
            messagebox.showinfo("Reset Complete", message)
        else:
            messagebox.showerror("Reset Error", message)
    
    def set_starting_ref(self):
        """Set starting internal reference (placeholder for future implementation)."""
        start_ref = self.start_ref_var.get().strip()
        if start_ref:
            messagebox.showinfo("Info", f"Starting reference set to: {start_ref}\n(Feature not yet implemented)")
        else:
            messagebox.showwarning("Warning", "Please enter a starting reference number")
    
    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo("About HPV Sample Tracker", 
                           "HPV Sample Tracker v1.0\n\n" +
                           "A desktop application for managing HPV sample records.\n\n" +
                           "Features:\n" +
                           "• Sample management with unique episode barcodes\n" +
                           "• Import/Export CSV and database files\n" +
                           "• Audit logging for all operations\n" +
                           "• Database backup functionality\n\n" +
                           "© 2025 HPV Sample Tracker")
    
    def on_closing(self):
        """Handle application closing."""
        # Save current window geometry
        self.app_config['window_geometry'] = self.geometry()
        save_config(self.app_config)
        
        # Close application
        self.destroy()

def main():
    """Main function to run the application."""
    app = HPVApp()
    app.mainloop()

if __name__ == "__main__":
    main()