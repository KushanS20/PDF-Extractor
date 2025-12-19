# Invoice to CSV Extractor (Regex Mode)

A lightweight offline tool to extract structured data from Invoice PDFs and export them to CSV.

## Features
- **Upload PDF Invoices**: Simple drag-and-drop interface.
- **Rule-Based Extraction**: Uses efficient text pattern matching (finding "Invoice #", "Total", etc.).
- **Offline & Free**: No AI API keys or internet required.
- **Structured Output**: Extracts Vendor Name, Invoice #, Date, Total, and Line Items (best-effort).
- **CSV Export**: Download the extracted data directly to Excel/CSV.

## Architecture
- **Backend**: Flask (Python) - Handles PDF parsing and text matching.
- **Frontend**: Streamlit (Python) - User interface.

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **No Keys Needed**: This version runs entirely locally.

## Usage
Double-click **`start_services.bat`** to run the application.
Then open **http://localhost:8501** in your browser."# PDF-Extractor" 
