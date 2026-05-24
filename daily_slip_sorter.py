import os
import shutil
from datetime import datetime

# Source folder
src = r"C:\Users\saait\Downloads\chinthalapudi_new_csv_pdfs2\Tharuni_Associates\Nuzvid"

# List all PDFs
pdfs = [f for f in os.listdir(src) if f.lower().endswith('.pdf')]

if not pdfs:
    print("No PDF files found in the folder.")
    exit()

print(f"Found {len(pdfs)} PDF files.\n")

for pdf in sorted(pdfs):
    filepath = os.path.join(src, pdf)
    
    # Get file modified date
    mod_time = os.path.getmtime(filepath)
    date_str = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d")
    
    # Create date folder if it doesn't exist
    date_folder = os.path.join(src, date_str)
    os.makedirs(date_folder, exist_ok=True)
    
    # Move file into date folder
    dest = os.path.join(date_folder, pdf)
    shutil.move(filepath, dest)
    print(f"  {pdf}  -->  {date_str}/")

print("\nDone! All PDFs sorted into date folders.")