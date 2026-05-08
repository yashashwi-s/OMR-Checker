import json
import csv
import glob
import os

def evaluate():
    # Load ground truth
    with open('sample/ground_truth.json', 'r') as f:
        truth = json.load(f)
        
    # Find the results CSV
    csv_files = glob.glob('omr_output/Results/*.csv')
    if not csv_files:
        print("No CSV results found!")
        return
        
    results_csv = csv_files[-1]  # Take the latest if multiple
    
    total_samples = 0
    total_app_correct = 0
    total_dob_correct = 0
    total_cat_correct = 0
    total_q_correct = 0
    total_questions = 0
    
    with open(results_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename_png = row['file_id']
            filename_pdf = filename_png.replace('.png', '.pdf')
            
            if filename_pdf not in truth:
                print(f"Ground truth not found for {filename_pdf}")
                continue
                
            gt = truth[filename_pdf]
            total_samples += 1
            
            # Check Application Number
            app_no_omr = "".join([row[f"app{i}"] for i in range(1, 11)])
            if app_no_omr == gt["application_number"]:
                total_app_correct += 1
            else:
                print(f"{filename_pdf} App No mismatch: {app_no_omr} != {gt['application_number']}")
                
            # Check DOB
            dob_omr = "".join([row[f"dob{i}"] for i in range(1, 9)])
            if dob_omr == gt["dob"]:
                total_dob_correct += 1
            else:
                print(f"{filename_pdf} DOB mismatch: {dob_omr} != {gt['dob']}")
                
            # Check Category
            if row["Category"] == gt["category"]:
                total_cat_correct += 1
            else:
                print(f"{filename_pdf} Category mismatch: {row['Category']} != {gt['category']}")
                
            # Check Answers
            for i in range(1, 41):
                q_omr = row[f"q{i}"]
                q_gt = gt["answers"][str(i)]
                total_questions += 1
                if q_omr == q_gt:
                    total_q_correct += 1
                    
    print("\n" + "="*40)
    print("EVALUATION RESULTS")
    print("="*40)
    print(f"Total Samples Evaluated: {total_samples}")
    print(f"Application Number Accuracy: {total_app_correct / total_samples * 100:.2f}% ({total_app_correct}/{total_samples})")
    print(f"Date of Birth Accuracy:      {total_dob_correct / total_samples * 100:.2f}% ({total_dob_correct}/{total_samples})")
    print(f"Category Accuracy:           {total_cat_correct / total_samples * 100:.2f}% ({total_cat_correct}/{total_samples})")
    print(f"Questions Accuracy:          {total_q_correct / total_questions * 100:.2f}% ({total_q_correct}/{total_questions})")
    print("="*40)

if __name__ == "__main__":
    evaluate()
