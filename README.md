# OMR Scanner & Grader

A simple, highly accurate, plug-and-play OMR grading pipeline.

## Installation

Clone the repository and install the required dependencies in a python/conda environment:
```bash
pip install -r requirements.txt
```

## Getting Started

1. **Print the Template**: 
   You can generate the blank OMR sheet PDF by running:
   ```bash
   python create.py
   ```
   *This will generate `IIT_BHU_Biochemical_OMR.pdf` which you can print and distribute.*

2. **Scan the Sheets**: 
   Collect the filled sheets and scan them as PDFs, PNGs, or JPGs. 
   Place all the scanned files directly into the `./sheets/` directory.

3. **Grade the Scans**:
   Ensure your correct answers are listed in `answer.txt` (40 lines, one letter per line). Then, simply run:
   ```bash
   python evaluate.py
   ```

## Output
The script will automatically process the sheets, read the filled bubbles, and calculate the final scores. You will find the results exported in two files in the main directory:
- `grades.csv`
- `grades.xlsx`

The grades will contain the following fields: `Application Number`, `DOB`, `Category`, and `Score`.

### Note for Synthetic Testing
If you wish to test the system without physically printing and scanning sheets, you can generate 50 simulated filled sheets by running:
```bash
python sample.py
```
This will automatically populate the `./sheets/` directory with randomly filled OMR sheets. You can then run `evaluate.py` to see the extraction in action.
