import json
import csv
import glob
import os
import sys
import subprocess
import fitz  # PyMuPDF
import pandas as pd

def convert_pdfs_to_images(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
    
    if not pdf_files:
        return
        
    print(f"Found {len(pdf_files)} PDFs in {input_dir}. Converting to PNG...")
    for pdf_path in pdf_files:
        doc = fitz.open(pdf_path)
        base_name = os.path.basename(pdf_path)
        name_without_ext = os.path.splitext(base_name)[0]
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=200)
            
            output_filename = f"{name_without_ext}.png" if len(doc) == 1 else f"{name_without_ext}_page{page_num+1}.png"
            output_path = os.path.join(output_dir, output_filename)
            pix.save(output_path)
    
    print("PDF conversion completed.")

def generate_and_copy_template(output_dir):
    print("Generating template.json...")
    subprocess.run([sys.executable, "generate_template.py"], check=True)
    
    if os.path.exists("template.json"):
        import shutil
        shutil.move("template.json", os.path.join(output_dir, "template.json"))

def run_omr_checker(images_dir, output_dir):
    print("\nRunning OMRChecker...")
    # Clear old results if they exist to prevent appending issues
    results_dir = os.path.join(output_dir, "Results")
    if os.path.exists(results_dir):
        import shutil
        shutil.rmtree(results_dir)
        
    cmd = [sys.executable, "OMRChecker/main.py", "--inputDir", images_dir, "--outputDir", output_dir]
    subprocess.run(cmd, check=True)

def calculate_grades_and_verify(omr_output_dir, sheets_dir):
    # 1. Load answer key
    try:
        with open('answer.txt', 'r') as f:
            answer_key = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print("Error: answer.txt not found in root directory.")
        sys.exit(1)
        
    if len(answer_key) != 40:
        print(f"Warning: answer.txt has {len(answer_key)} answers, expected 40.")



    # 3. Find the latest CSV
    csv_files = glob.glob(os.path.join(omr_output_dir, 'Results', '*.csv'))
    if not csv_files:
        print(f"Error: No CSV results found in {os.path.join(omr_output_dir, 'Results')}")
        sys.exit(1)
        
    results_csv = max(csv_files, key=os.path.getmtime)
    print(f"\nProcessing extracted data from: {results_csv}")

    # 4. Process
    grades_data = []
    
    with open(results_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename_png = row['file_id']
            filename_pdf = filename_png.replace('.png', '.pdf')
            
            # Reconstruct fields
            app_no = "".join([row.get(f"app{i}", "") for i in range(1, 11)])
            dob = "".join([row.get(f"dob{i}", "") for i in range(1, 9)])
            category = row.get("Category", "")
            
            score_omr = 0
            for i in range(1, 41):
                ans = row.get(f"q{i}", "")
                if i - 1 < len(answer_key) and ans == answer_key[i-1]:
                    score_omr += 1
                    
            grades_data.append({
                "Application Number": app_no,
                "DOB": dob,
                "Category": category,
                "Score": score_omr
            })

    # 5. Export
    df = pd.DataFrame(grades_data)
    df.to_csv('grades.csv', index=False)
    df.to_excel('grades.xlsx', index=False)
    
    print(f"\nSuccessfully evaluated {len(grades_data)} sheets.")
    print("Grades exported to: grades.csv and grades.xlsx")

def main():
    sheets_dir = "./sheets"
    images_dir = os.path.join(sheets_dir, "images")
    omr_output_dir = os.path.join(sheets_dir, "omr_output")
    
    if not os.path.exists(sheets_dir):
        print(f"Creating directory: {sheets_dir}")
        os.makedirs(sheets_dir)
        print("Please place your PDF or PNG sheets in the './sheets/' directory and run this script again.")
        sys.exit(0)

    # 1. Convert PDFs
    convert_pdfs_to_images(sheets_dir, images_dir)
    
    # 2. Check if we have any images to process
    img_files = glob.glob(os.path.join(images_dir, "*.png"))
    if not img_files:
        # Check if user put images directly in sheets_dir
        direct_images = glob.glob(os.path.join(sheets_dir, "*.png")) + glob.glob(os.path.join(sheets_dir, "*.jpg"))
        if direct_images:
            os.makedirs(images_dir, exist_ok=True)
            import shutil
            for img in direct_images:
                shutil.move(img, os.path.join(images_dir, os.path.basename(img)))
            img_files = glob.glob(os.path.join(images_dir, "*.png"))
            
    if not img_files:
        print(f"No PDFs or images found in {sheets_dir}. Please add sheets and run again.")
        sys.exit(0)
        
    # 3. Generate Template
    generate_and_copy_template(images_dir)
    
    # 4. Run OMR
    run_omr_checker(images_dir, omr_output_dir)
    
    # 5. Grade
    calculate_grades_and_verify(omr_output_dir, sheets_dir)

if __name__ == "__main__":
    main()
