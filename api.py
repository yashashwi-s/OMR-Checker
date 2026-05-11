import os
import shutil
import subprocess
import sys
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

app = FastAPI(title="OMR Checker API")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup directories
os.makedirs("sheets", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.post("/process")
async def process_files(
    answer_file: Optional[UploadFile] = File(None),
    sheet_files: List[UploadFile] = File(...)
):
    try:
        # Clear existing sheets directory to prevent old results from mixing
        if os.path.exists("sheets"):
            shutil.rmtree("sheets")
        os.makedirs("sheets", exist_ok=True)
        
        # Save answer.txt if provided
        if answer_file and answer_file.filename:
            with open("answer.txt", "wb") as f:
                shutil.copyfileobj(answer_file.file, f)
                
        # Validate that we have an answer.txt
        if not os.path.exists("answer.txt"):
            return {"error": "answer.txt is missing. Please upload an answer key."}
                
        # Save uploaded sheets
        saved_sheets = 0
        for sheet in sheet_files:
            if sheet.filename:
                basename = os.path.basename(sheet.filename)
                path = os.path.join("sheets", basename)
                with open(path, "wb") as f:
                    shutil.copyfileobj(sheet.file, f)
                saved_sheets += 1
                
        if saved_sheets == 0:
            return {"error": "No valid sheet files were uploaded."}
            
        # Run the evaluation pipeline
        try:
            subprocess.run([sys.executable, "evaluate.py"], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else e.stdout
            return {"error": f"Evaluation pipeline failed:\n{error_msg}"}
            
        # Read the resulting grades.csv
        if not os.path.exists("grades.csv"):
            return {"error": "Evaluation finished but grades.csv was not found. Check if the sheets matched the template."}
            
        df = pd.read_csv("grades.csv")
        results = df.to_dict(orient="records")
        
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
