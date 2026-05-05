# OMR Scanner — Accuracy Evaluation Report

**Images scanned:** 11  
**Matched to ground truth:** 8  
**Unmatched:** 3


## Overall Answer Accuracy

**160 / 300  (53.3%)**

## Per-Field Accuracy

| Field | Correct | Total | Accuracy |
|-------|---------|-------|----------|
| roll_no | 0 | 8 | 0.0% |
| dob | 6 | 8 | 75.0% |
| gender | 6 | 8 | 75.0% |
| paper_set | 5 | 8 | 62.5% |
| category | 6 | 8 | 75.0% |
| sub_category | 6 | 8 | 75.0% |

## Per-Augmentation Accuracy

| Augmentation | Correct | Total | Accuracy |
|-------------|---------|-------|----------|
| clean | 81 | 150 | 54.0% |
| gauss_noise | 53 | 100 | 53.0% |
| jpeg | 57 | 100 | 57.0% |
| motion_blur | 22 | 50 | 44.0% |
| page_curl | 31 | 50 | 62.0% |
| salt_pepper | 26 | 50 | 52.0% |
| shadow | 26 | 50 | 52.0% |

## Errors

- omr_0001_aug02.png: no ground-truth JSON found
- omr_0002_aug02.png: no ground-truth JSON found
- omr_0003_aug02.png: no ground-truth JSON found