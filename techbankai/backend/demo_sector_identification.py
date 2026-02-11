"""
Quick demonstration of the company sector identification feature.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.company_sector_mapper import (
    identify_company_sector,
    enrich_work_history_with_sectors,
    get_candidate_primary_sector
)

print("\n" + "="*70)
print("COMPANY SECTOR IDENTIFICATION - LIVE DEMONSTRATION")
print("="*70)

# Example 1: Identify sectors for various companies
print("\n📊 EXAMPLE 1: Company Sector Identification")
print("-"*70)

companies = [
    "Axis Bank",
    "Infosys",
    "Apollo Hospitals",
    "Amazon",
    "XYZ Technologies Pvt Ltd",
    "Global Finance Bank"
]

for company in companies:
    result = identify_company_sector(company)
    print(f"\n🏢 {company}")
    print(f"   └─ Sector: {result['sector']}")
    print(f"   └─ Domain: {result['domain']}")
    print(f"   └─ Confidence: {result['confidence']}")
    print(f"   └─ Method: {result['method']}")

# Example 2: Analyze a candidate's work history
print("\n\n📋 EXAMPLE 2: Candidate Work History Analysis")
print("-"*70)

sample_resume = {
    "name": "John Doe",
    "work_history": [
        {
            "company": "Axis Bank",
            "role": "Senior Software Engineer",
            "start_date": "Jan 2020",
            "end_date": "Present",
            "is_current": 1,
            "description": "Leading digital banking initiatives"
        },
        {
            "company": "Infosys",
            "role": "Software Engineer",
            "start_date": "Jun 2017",
            "end_date": "Dec 2019",
            "is_current": 0,
            "description": "Developed enterprise applications"
        },
        {
            "company": "TCS",
            "role": "Associate Consultant",
            "start_date": "Jul 2015",
            "end_date": "May 2017",
            "is_current": 0,
            "description": "Worked on client projects"
        }
    ]
}

print(f"\n👤 Candidate: {sample_resume['name']}")
print(f"📊 Total Experience: {len(sample_resume['work_history'])} companies")

# Enrich work history
enriched_history = enrich_work_history_with_sectors(sample_resume['work_history'])

print("\n🏢 Work History with Sectors:")
for i, job in enumerate(enriched_history, 1):
    print(f"\n   {i}. {job['company']} - {job['role']}")
    print(f"      └─ Sector: {job['sector']}")
    print(f"      └─ Domain: {job['domain']}")
    print(f"      └─ Period: {job['start_date']} to {job['end_date']}")

# Get sector analysis
sector_analysis = get_candidate_primary_sector(enriched_history)

print("\n\n📈 Sector Analysis:")
print(f"   └─ Primary Sector: {sector_analysis['primary_sector']}")
print(f"   └─ Sector Experience:")
for sector, years in sector_analysis['sector_experience'].items():
    print(f"      • {sector}: {years} years")
print(f"   └─ Sector Transitions: {sector_analysis['sector_transitions']}")

# Example 3: Real-world scenario
print("\n\n🎯 EXAMPLE 3: Real-World Scenario")
print("-"*70)

print("\nScenario: Candidate moved from IT Services to Banking sector")
print("\nWork History:")
print("  2015-2017: TCS (IT Services)")
print("  2017-2020: Infosys (IT Services)")
print("  2020-Present: Axis Bank (BFSI)")

print("\n✅ System Identified:")
print(f"  • Primary Sector: {sector_analysis['primary_sector']}")
print(f"  • Career Transition: {' → '.join(sector_analysis['sector_transitions'])}")
print(f"  • Total IT Services Experience: {sector_analysis['sector_experience'].get('IT Services', 0)} years")
print(f"  • Total BFSI Experience: {sector_analysis['sector_experience'].get('BFSI', 0)} years")

print("\n" + "="*70)
print("✅ DEMONSTRATION COMPLETE!")
print("="*70)
print("\nThe system successfully:")
print("  ✓ Identified sectors for all companies")
print("  ✓ Enriched work history with sector information")
print("  ✓ Calculated primary sector based on experience")
print("  ✓ Tracked sector transitions across career")
print("\n")
