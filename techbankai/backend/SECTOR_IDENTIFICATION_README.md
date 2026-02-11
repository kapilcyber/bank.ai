# Company Sector Identification Feature

## Overview

This feature automatically extracts company details from resumes and identifies the industry sector/domain based on company names. For example:
- **Axis Bank** → BFSI (Banking)
- **Infosys** → IT Services (Software Consulting)
- **Apollo Hospitals** → Healthcare (Hospital Services)

## Features

### 1. **Automatic Sector Identification**
- Identifies industry sector and domain for each company in work history
- Uses a 3-tier approach:
  1. **Database Lookup**: Exact match from predefined company database (121+ companies)
  2. **Keyword Matching**: Pattern-based identification using company name keywords
  3. **AI-Powered**: Optional GPT-4 identification for unknown companies

### 2. **Candidate Sector Analysis**
- **Primary Sector**: Identifies the candidate's main industry based on total years of experience
- **Sector Experience**: Breakdown of years worked in each sector
- **Sector Transitions**: Tracks career transitions between sectors (e.g., "Banking → IT Services")

### 3. **Work History Enrichment**
Each work history entry now includes:
- `sector`: Industry sector (e.g., "BFSI", "IT Services", "Healthcare")
- `domain`: Sub-domain (e.g., "Banking", "Software Consulting", "Hospital Services")
- `sector_confidence`: Confidence level (high/medium/low/none)

## Supported Sectors

The system recognizes the following industry sectors:

| Sector | Examples | Domains |
|--------|----------|---------|
| **BFSI** | Axis Bank, HDFC, ICICI, Paytm | Banking, Insurance, Fintech, Asset Management |
| **IT Services** | TCS, Infosys, Wipro, HCL | Software Consulting, Software Products |
| **E-commerce** | Amazon, Flipkart, Myntra | Retail, Fashion, Food Delivery, Quick Commerce |
| **Healthcare** | Apollo, Fortis, Dr. Reddy's | Hospital Services, Pharmaceuticals, Health Tech |
| **Manufacturing** | Tata Motors, Reliance, L&T | Automotive, Steel, FMCG, Engineering |
| **Telecom** | Airtel, Jio, Vodafone | Telecommunications |
| **Education** | BYJU'S, Unacademy, upGrad | EdTech |
| **Consulting** | McKinsey, Deloitte, PwC | Management Consulting, Professional Services |
| **Technology** | Google, Meta, Microsoft | Internet Services, Social Media, Consumer Electronics |

## Database Schema Changes

### New Columns in `experiences` Table

```sql
ALTER TABLE experiences 
ADD COLUMN sector VARCHAR(100);  -- e.g., "BFSI", "IT Services"

ALTER TABLE experiences 
ADD COLUMN domain VARCHAR(100);  -- e.g., "Banking", "Software Consulting"
```

### Migration

Run the migration to add the new columns:

```bash
cd backend
python -m src.migrations.add_sector_to_experiences
```

To rollback:

```bash
python -m src.migrations.add_sector_to_experiences downgrade
```

## API Response Format

### Resume with Sector Information

```json
{
  "id": 123,
  "filename": "john_doe_resume.pdf",
  "parsed_data": {
    "resume_candidate_name": "John Doe",
    "primary_sector": "BFSI",
    "sector_experience": {
      "BFSI": 5.5,
      "IT Services": 2.0
    },
    "sector_transitions": ["IT Services → BFSI"]
  },
  "work_history": [
    {
      "company": "Axis Bank",
      "role": "Software Engineer",
      "start_date": "Jan 2020",
      "end_date": "Present",
      "is_current": 1,
      "sector": "BFSI",
      "domain": "Banking",
      "sector_confidence": "high"
    },
    {
      "company": "Infosys",
      "role": "Associate Consultant",
      "start_date": "Jan 2018",
      "end_date": "Dec 2019",
      "is_current": 0,
      "sector": "IT Services",
      "domain": "Software Consulting",
      "sector_confidence": "high"
    }
  ]
}
```

## Usage Examples

### 1. Identify Sector for a Single Company

```python
from src.services.company_sector_mapper import identify_company_sector

result = identify_company_sector("Axis Bank")
print(result)
# Output:
# {
#   'sector': 'BFSI',
#   'domain': 'Banking',
#   'confidence': 'high',
#   'method': 'database'
# }
```

### 2. Enrich Work History with Sectors

```python
from src.services.company_sector_mapper import enrich_work_history_with_sectors

work_history = [
    {"company": "Axis Bank", "role": "Engineer", ...},
    {"company": "Infosys", "role": "Consultant", ...}
]

enriched = enrich_work_history_with_sectors(work_history)
# Each entry now has 'sector', 'domain', and 'sector_confidence' fields
```

### 3. Get Candidate's Primary Sector

```python
from src.services.company_sector_mapper import get_candidate_primary_sector

sector_analysis = get_candidate_primary_sector(work_history)
print(sector_analysis)
# Output:
# {
#   'primary_sector': 'BFSI',
#   'sector_experience': {'BFSI': 5.5, 'IT Services': 2.0},
#   'sector_transitions': ['IT Services → BFSI'],
#   'total_companies': 2
# }
```

## Testing

### Run Test Suite

```bash
cd backend
python test_sector_identification.py
```

The test suite includes:
1. **Predefined Company Mapping**: Tests exact matches from database
2. **Keyword-Based Matching**: Tests pattern-based identification
3. **Work History Enrichment**: Tests sector analysis and transitions
4. **Edge Cases**: Tests empty strings, unknown companies, etc.

### Expected Output

```
============================================================
COMPANY SECTOR IDENTIFICATION - TEST SUITE
============================================================

TEST 1: Predefined Company Mapping
...
Axis Bank:
  Sector: BFSI
  Domain: Banking
  Confidence: high
  Method: database

TEST 2: Keyword-Based Matching
...
XYZ Bank Ltd:
  Sector: BFSI
  Domain: Financial Services
  Confidence: medium
  Method: keyword

TEST 3: Work History Enrichment
...
Primary Sector: BFSI
Sector Experience: {'BFSI': 3.0, 'IT Services': 2.0}
Sector Transitions: ['IT Services → BFSI']

============================================================
ALL TESTS COMPLETED SUCCESSFULLY!
============================================================
```

## Adding New Companies

To add new companies to the database, edit:
```
backend/src/data/company_sector_database.json
```

Format:
```json
{
  "BFSI": {
    "Your Bank Name": {
      "sector": "BFSI",
      "domain": "Banking"
    }
  }
}
```

The system will automatically reload the database on next use.

## AI-Powered Identification (Optional)

For unknown companies, you can enable AI-powered sector identification:

```python
result = identify_company_sector("Unknown Startup Inc", use_ai=True)
```

This uses GPT-4 to identify the sector. Requires OpenAI API key to be configured.

## Performance

- **Database Lookup**: ~0.001ms per company (cached)
- **Keyword Matching**: ~0.01ms per company
- **AI Identification**: ~500-1000ms per company (only for unknown companies)

The system caches all results to minimize repeated lookups.

## Integration Points

The sector identification is automatically integrated into:

1. **Resume Parser** (`src/services/resume_parser.py`)
   - Enriches work history during resume parsing
   - Calculates primary sector and sector experience

2. **Resume API** (`src/routes/resume.py`)
   - Returns sector information in resume responses
   - Includes sector analysis in resume details

3. **Database Models** (`src/models/resume.py`)
   - Stores sector and domain in `experiences` table
   - Stores sector analysis in `parsed_data` JSONB field

## Future Enhancements

Potential improvements:
- Sector-based candidate filtering in JD analysis
- Sector relevance scoring in matching engine
- Industry transition insights and analytics
- Sector-specific skill recommendations
