import os
import fitz  # PyMuPDF
import glob

def convert_pdfs_to_images(pdf_dir, output_dir, dpi=200):
    os.makedirs(output_dir, exist_ok=True)
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    
    print(f"Found {len(pdf_files)} PDFs in {pdf_dir}")
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        name, _ = os.path.splitext(filename)
        output_path = os.path.join(output_dir, f"{name}.png")
        
        # Open PDF
        doc = fitz.open(pdf_path)
        # We only care about the first page
        page = doc.load_page(0)
        
        # Render page to an image pixel map
        pix = page.get_pixmap(dpi=dpi)
        
        # Save as PNG
        pix.save(output_path)
        doc.close()
        
    print(f"Successfully converted {len(pdf_files)} PDFs to images in {output_dir}")

if __name__ == "__main__":
    convert_pdfs_to_images("./sample", "./sample_images")
