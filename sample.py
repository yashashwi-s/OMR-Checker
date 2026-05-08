import os
import json
import random
import string
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def draw_bubble(c, x, y, radius=5, filled=False):
    c.circle(x, y, radius, stroke=1, fill=1 if filled else 0)

def draw_box(c, x, y, width, height, text=""):
    c.rect(x, y, width, height, stroke=1, fill=0)
    if text:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x + 4, y + 4, str(text))

def generate_random_data():
    first_name = ''.join(random.choices(string.ascii_uppercase, k=random.randint(4, 8)))
    last_name = ''.join(random.choices(string.ascii_uppercase, k=random.randint(4, 8)))
    
    app_no = ''.join(random.choices(string.digits, k=10))
    
    day = str(random.randint(1, 28)).zfill(2)
    month = str(random.randint(1, 12)).zfill(2)
    year = str(random.randint(1995, 2005))
    dob = f"{day}{month}{year}"
    
    category = random.choice(["GEN", "EWS", "OBC", "SC", "ST"])
    answers = {str(i): random.choice(['A', 'B', 'C', 'D']) for i in range(1, 41)}
    
    return {
        "name": f"{first_name} {last_name}",
        "application_number": app_no,
        "dob": dob,
        "category": category,
        "answers": answers
    }

def generate_filled_omr(filepath, data):
    c = canvas.Canvas(filepath, pagesize=A4)
    
    # Draw a border for edge detection
    c.setLineWidth(2)
    c.rect(20, 20, 555, 800, stroke=1, fill=0)
    c.setLineWidth(1)
    
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(297, 800, "Biochemical Department, IIT BHU (Varanasi)")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 745, "Name: ")
    c.setFont("Helvetica", 12)
    c.drawString(95, 745, data["name"])
    c.line(95, 743, 330, 743)
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(380, 760, "General Instructions:")
    c.setFont("Helvetica", 9)
    c.drawString(380, 745, "1. Use only black or blue ballpoint pen.")
    c.drawString(380, 730, "2. Darken the bubble completely.")
    c.drawString(380, 715, "3. Do not make any stray marks on the sheet.")
    c.drawString(380, 700, "4. Correct way: \u25CF  Incorrect way: \u2714 \u2716")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 650, "Application Number")
    
    c.setFont("Helvetica-Bold", 8)
    for j in range(10):
        c.drawString(40, 612 - j*16, str(j))
        
    app_no = data["application_number"]
    for i in range(10):
        digit = int(app_no[i])
        draw_box(c, 50 + i*16, 630, 16, 16, text=str(digit))
        for j in range(10):
            is_filled = (j == digit)
            draw_bubble(c, 58 + i*16, 615 - j*16, filled=is_filled)
            
    c.setFont("Helvetica-Bold", 10)
    c.drawString(250, 650, "Date of Birth (DDMMYYYY)")
    
    c.setFont("Helvetica-Bold", 8)
    for j in range(10):
        c.drawString(240, 612 - j*16, str(j))
        
    dob = data["dob"]
    for i in range(8):
        digit = int(dob[i])
        draw_box(c, 250 + i*16, 630, 16, 16, text=str(digit))
        for j in range(10):
            is_filled = (j == digit)
            draw_bubble(c, 258 + i*16, 615 - j*16, filled=is_filled)
            
    c.setFont("Helvetica-Bold", 10)
    c.drawString(420, 650, "Category")
    draw_box(c, 420, 630, 50, 16, text=data["category"])
    
    categories = ["GEN", "EWS", "OBC", "SC", "ST"]
    cat_index = categories.index(data["category"])
    
    for i, cat in enumerate(categories):
        c.setFont("Helvetica-Bold", 9)
        c.drawString(425, 611 - i*16, cat)
        is_filled = (i == cat_index)
        draw_bubble(c, 463, 615 - i*16, filled=is_filled)
        
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 430, "Answers (1-40)")
    c.line(50, 425, 545, 425)
    
    options_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    
    for col in range(4):
        x_offset = 50 + col * 125
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x_offset, 400, "Q.No")
        c.drawString(x_offset + 33, 400, "A")
        c.drawString(x_offset + 53, 400, "B")
        c.drawString(x_offset + 73, 400, "C")
        c.drawString(x_offset + 93, 400, "D")
        
        for row in range(10):
            y_offset = 375 - row * 22
            q_num = col * 10 + row + 1
            q_str = str(q_num)
            
            c.setFont("Helvetica-Bold", 10)
            if q_num < 10:
                c.drawString(x_offset + 8, y_offset - 3, q_str)
            else:
                c.drawString(x_offset + 4, y_offset - 3, q_str)
                
            correct_opt_idx = options_map[data["answers"][q_str]]
            
            for opt in range(4):
                is_filled = (opt == correct_opt_idx)
                draw_bubble(c, x_offset + 37 + opt * 20, y_offset, radius=6, filled=is_filled)
                
    c.save()

def create_dataset(num_samples=5):
    # Create the sample directory if it doesn't exist
    output_dir = "./sample"
    os.makedirs(output_dir, exist_ok=True)
    
    dataset_truth = {}
    
    for i in range(1, num_samples + 1):
        data = generate_random_data()
        filename = f"Filled_OMR_{i:03d}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        generate_filled_omr(filepath, data)
        dataset_truth[filename] = data
        
        print(f"Generated: {filepath}")
        
    # Save the master JSON ground truth inside the sample directory
    json_path = os.path.join(output_dir, "ground_truth.json")
    with open(json_path, "w") as f:
        json.dump(dataset_truth, f, indent=4)
        
    print(f"\nSuccess! Generated {num_samples} PDFs and {json_path}")

if __name__ == "__main__":
    create_dataset(num_samples=50)
