from flask import Flask, request, jsonify
import pdfplumber
import os
from werkzeug.utils import secure_filename
import re
from flask_cors import CORS
import json
import uuid
import datetime

app = Flask(__name__)
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
@app.route('/')
def health():
    return "Invoice Extractor Backend is Running (Advanced Rule-Based)!", 200

def parse_table(page):
    """
    Attempts to extract a table from the page and map columns to standard fields.
    Returns a list of item dicts.
    """
    items = []
    # Extract table with default settings
    tables = page.extract_tables()
    
    for table in tables:
        if not table or len(table) < 2:
            continue
            
        # 1. Identify Header Row
        header_row_idx = -1
        headers = []
        
        # Look for a row that looks like a header (contains 'qty', 'price', 'desc', etc.)
        for idx, row in enumerate(table):
            # Clean row values
            row_text = [str(cell).lower() for cell in row if cell]
            joined = " ".join(row_text)
            
            # Simple keyword check
            if any(k in joined for k in ['qty', 'quantity', 'price', 'amount', 'total', 'description', 'disc', 'item']):
                header_row_idx = idx
                headers = [str(cell).lower().strip() if cell else "" for cell in row]
                break
        
        if header_row_idx == -1:
            continue
            
        # 2. Map Columns
        col_map = {
            "description": -1,
            "quantity": -1,
            "unit_price": -1,
            "total_price": -1
        }
        
        for idx, h in enumerate(headers):
            if any(x in h for x in ['desc', 'item', 'product', 'particular']):
                col_map['description'] = idx
            elif any(x in h for x in ['qty', 'quantity', 'count']):
                col_map['quantity'] = idx
            elif any(x in h for x in ['price', 'rate', 'unit']):
                col_map['unit_price'] = idx
            elif any(x in h for x in ['amount', 'total', 'value', 'sum']):
                col_map['total_price'] = idx
        
        # 3. Extract Data Rows
        for row in table[header_row_idx+1:]:
            # Skip empty rows or subtotal rows
            if not row or all(c is None or c == "" for c in row):
                continue
            
            # Check if it's a footer row (Subtotal, Total, etc.)
            row_str = " ".join([str(c).lower() for c in row if c])
            if any(x in row_str for x in ['total', 'subtotal', 'tax', 'vat']):
                continue
                
            item = {}
            # Fallbacks if columns aren't mapped
            if col_map['description'] != -1 and len(row) > col_map['description']:
                item['description'] = row[col_map['description']]
            
            if col_map['quantity'] != -1 and len(row) > col_map['quantity']:
                item['quantity'] = row[col_map['quantity']]
                
            if col_map['unit_price'] != -1 and len(row) > col_map['unit_price']:
                item['unit_price'] = row[col_map['unit_price']]
                
            if col_map['total_price'] != -1 and len(row) > col_map['total_price']:
                item['total_price'] = row[col_map['total_price']]
            
            # Additional Heuristic: If we found nothing but good table exists
            if not item and len(row) >= 3:
                # Guess: Description is usually wide (or first), Qty and Price are numbers
                # Let's verify if we have numbers
                pass # Logic can be expanded here
            
            if item.get('description') or item.get('total_price'):
                 items.append(item)

    return items

def extract_invoice_data_sync(file_path):
    """
    Synchronous function to process Invoice PDF using Advanced Rules
    """
    try:
        data = {
            "vendor_name": None,
            "vendor_address": None,
            "invoice_number": None,
            "invoice_date": None,
            "total_amount": None,
            "currency": "$", 
            "line_items": []
        }
        
        all_text = ""
        
        with pdfplumber.open(file_path) as pdf:
            # 1. Text Parsing (Global)
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text += text + "\n"
                
                # 2. Table Extraction (Per Page)
                page_items = parse_table(page)
                if page_items:
                    data['line_items'].extend(page_items)
        
        if not all_text.strip():
            raise ValueError("No text could be extracted from this PDF.")
            
        # --- Metadata Regex ---
        
        # Vendor Name: 
        # Heuristic: Largest text on the first page roughly top-left? 
        # For now, stick to first non-empty lines, but check for exclusions
        lines = [l.strip() for l in all_text.split('\n') if l.strip()]
        for line in lines[:5]:
            # Skip "Invoice", "Bill To", etc.
            if any(x in line.lower() for x in ['invoice', 'bill to', 'ship to', 'order']):
                continue
            if len(line) > 3:
                data['vendor_name'] = line
                break
        
        # Invoice Number
        # Expanded patterns: "INV NO:", "Bill #", "Order #" (sometimes confused)
        inv_match = re.search(r'(?i)(invoice\s*(?:no\.?|number|#)|inv\.?\s*no\.?|bill\s*(?:no\.?|#))\s*[:#]?\s*([a-zA-Z0-9\/-]{3,})', all_text)
        if inv_match:
            data['invoice_number'] = inv_match.group(2).strip()
            
        # Date
        # YYYY-MM-DD or DD-MMM-YY, etc.
        date_match = re.search(r'(\d{4}[-]\d{2}[-]\d{2}|\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})', all_text)
        if date_match:
            data['invoice_date'] = date_match.group(1).strip()
            
        # Total Amount
        # "Total Amount", "Grand Total", "Total:"
        # Captures just the number part
        total_match = re.search(r'(?i)(total\s*(?:amount|due|value)?|grand\s*total|amount\s*due)\s*[:]?\s*([$€£]?\s*[\d,]+\.?\d{2})', all_text)
        if total_match:
            data['total_amount'] = total_match.group(2).strip()
            
        return data
        
    except Exception as e:
        print(f"Error extracting data: {e}")
        return {"error": str(e)}

@app.route('/extract-invoice-data', methods=['POST'])
def extract_invoice_data():
    """
    Upload PDF and process synchronously
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.endswith('.pdf'):
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        filename = secure_filename(file.filename or "")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}")
        
        # Save file
        file.save(file_path)
        
        # Process synchronously
        result = extract_invoice_data_sync(file_path)
        
        if "error" in result:
             return jsonify({'error': result["error"]}), 500

        return jsonify({
            'file_id': file_id,
            'status': 'success',
            'extracted_data': result
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True)