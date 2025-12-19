import streamlit as st
import requests
import time
import pandas as pd
from io import BytesIO

st.set_page_config(layout="wide", page_title="Invoice Extractor")

st.title("📄 Smart Invoice to CSV Extractor")
st.markdown("Upload an invoice (PDF) and extract structured data (Vendor, Date, Items) into CSV.")

uploaded_file = st.file_uploader('Choose an Invoice PDF', type='pdf')

if uploaded_file:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Invoice Preview")
        # Display PDF
        import base64
        base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

    with col2:
        st.subheader("Extraction Results")
        
        if st.button("Extract Data"):
            with st.spinner("Processing invoice... (this may take a few seconds)"):
                files = {'file': (uploaded_file.name, uploaded_file, 'application/pdf')}
                try:
                    # 1. Start Processing & Wait (Synchronous)
                    response = requests.post('http://127.0.0.1:5000/extract-invoice-data', files=files)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            extracted_data = data.get('extracted_data', {})
                            
                            st.success("Extraction Complete!")
                            
                            # Display General Info
                            st.markdown("### 🏢 Vendor Details")
                            st.write(f"**Name:** {extracted_data.get('vendor_name')}")
                            st.write(f"**Address:** {extracted_data.get('vendor_address')}")
                            
                            st.markdown("### 🧾 Invoice Details")
                            st.write(f"**Number:** {extracted_data.get('invoice_number')}")
                            st.write(f"**Date:** {extracted_data.get('invoice_date')}")
                            st.write(f"**Total Amount:** {extracted_data.get('total_amount')} {extracted_data.get('currency')}")
                            
                            # Display Items
                            st.markdown("### 📦 Line Items")
                            line_items = extracted_data.get('line_items', [])
                            if line_items:
                                df_items = pd.DataFrame(line_items)
                                st.dataframe(df_items, use_container_width=True)
                                
                                # Prepare CSV
                                flat_data = []
                                for item in line_items:
                                    row = {
                                        "Vendor Name": extracted_data.get('vendor_name'),
                                        "Invoice Number": extracted_data.get('invoice_number'),
                                        "Invoice Date": extracted_data.get('invoice_date'),
                                        "Description": item.get('description'),
                                        "Quantity": item.get('quantity'),
                                        "Unit Price": item.get('unit_price'),
                                        "Total Price": item.get('total_price')
                                    }
                                    flat_data.append(row)
                                
                                df_export = pd.DataFrame(flat_data)
                                csv = df_export.to_csv(index=False).encode('utf-8')
                                
                                st.download_button(
                                    label="📥 Download CSV",
                                    data=csv,
                                    file_name=f"invoice_{extracted_data.get('invoice_number', 'export')}.csv",
                                    mime='text/csv',
                                )
                            else:
                                st.warning("No line items found.")
                        except ValueError:
                            st.error(f"Backend returned invalid JSON: {response.text[:200]}")
                    else:
                        error_msg = "Unknown Error"
                        try:
                            error_msg = response.json().get('error', 'Unknown Error')
                        except:
                            error_msg = response.text
                        st.error(f"Error ({response.status_code}): {error_msg}")

                except Exception as e:
                    st.error(f"Connection Error: {e}")

 