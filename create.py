from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def draw_bubble(c, x, y, radius=5):
    c.circle(x, y, radius, stroke=1, fill=0)

def draw_box(c, x, y, width, height):
    c.rect(x, y, width, height, stroke=1, fill=0)

def generate_omr(filename):
    c = canvas.Canvas(filename, pagesize=A4)
    
    # Draw a border for edge detection
    c.setLineWidth(2)
    c.rect(20, 20, 555, 800, stroke=1, fill=0)
    c.setLineWidth(1)
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(297, 800, "Biochemical Department, IIT BHU (Varanasi)")
    
    # Name section
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 745, "Name: ")
    c.line(95, 745, 330, 745)
    
    # Instructions
    c.setFont("Helvetica-Bold", 10)
    c.drawString(380, 760, "General Instructions:")
    c.setFont("Helvetica", 9)
    c.drawString(380, 745, "1. Use only black or blue ballpoint pen.")
    c.drawString(380, 730, "2. Darken the bubble completely.")
    c.drawString(380, 715, "3. Do not make any stray marks on the sheet.")
    c.drawString(380, 700, "4. Correct way: \u25CF  Incorrect way: \u2714 \u2716")
    
    # --- Application Number ---
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 650, "Application Number")
    
    # Add 0-9 labels to the left of the Application Number rows
    c.setFont("Helvetica-Bold", 8)
    for j in range(10):
        c.drawString(40, 612 - j*16, str(j))
        
    for i in range(10):
        draw_box(c, 50 + i*16, 630, 16, 16)
        for j in range(10):
            draw_bubble(c, 58 + i*16, 615 - j*16)
            
    # --- Date of Birth ---
    c.setFont("Helvetica-Bold", 10)
    c.drawString(250, 650, "Date of Birth (DDMMYYYY)")
    
    # Add 0-9 labels to the left of the DOB rows
    c.setFont("Helvetica-Bold", 8)
    for j in range(10):
        c.drawString(240, 612 - j*16, str(j))
        
    for i in range(8):
        draw_box(c, 250 + i*16, 630, 16, 16)
        for j in range(10):
            draw_bubble(c, 258 + i*16, 615 - j*16)
            
    # --- Category ---
    c.setFont("Helvetica-Bold", 10)
    c.drawString(420, 650, "Category")
    
    # Bigger box starting below the 'Category' word
    draw_box(c, 420, 630, 50, 16)
    
    categories = ["GEN", "EWS", "OBC", "SC", "ST"]
    for i, cat in enumerate(categories):
        c.setFont("Helvetica-Bold", 9)
        c.drawString(425, 611 - i*16, cat)
        draw_bubble(c, 463, 615 - i*16)
        
    # --- Answers (1-40) ---
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 430, "Answers (1-40)")
    c.line(50, 425, 545, 425)
    
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
            
            c.setFont("Helvetica-Bold", 10)
            if q_num < 10:
                c.drawString(x_offset + 8, y_offset - 3, str(q_num))
            else:
                c.drawString(x_offset + 4, y_offset - 3, str(q_num))
                
            for opt in range(4):
                draw_bubble(c, x_offset + 37 + opt * 20, y_offset, radius=6)
                
    c.save()

generate_omr("IIT_BHU_Biochemical_OMR.pdf")
