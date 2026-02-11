"""
Test script for company sector identification feature.

This script tests the company sector mapper service with various company names.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.company_sector_mapper import (
    identify_company_sector,
    get_candidate_primary_sector,
    enrich_work_history_with_sectors
)


def test_predefined_companies():
    """Test sector identification for predefined companies."""
    print("\n" + "="*60)
    print("TEST 1: Predefined Company Mapping")
    print("="*60)
    
    test_companies = [
        "Axis Bank",
        "TCS",
        "Infosys",
        "Apollo Hospitals",
        "Amazon",
        "Flipkart",
        "HDFC Bank",
        "Wipro"
    ]
    
    for company in test_companies:
        result = identify_company_sector(company)
        print(f"\n{company}:")
        print(f"  Sector: {result['sector']}")
        print(f"  Domain: {result['domain']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Method: {result['method']}")


def test_keyword_matching():
    """Test keyword-based sector identification."""
    print("\n" + "="*60)
    print("TEST 2: Keyword-Based Matching")
    print("="*60)
    
    test_companies = [
        "XYZ Bank Ltd",
        "ABC Technologies",
        "Global Hospital",
        "Indian Manufacturing Industries",
        "Tech Solutions Pvt Ltd"
    ]
    
    for company in test_companies:
        result = identify_company_sector(company)
        print(f"\n{company}:")
        print(f"  Sector: {result['sector']}")
        print(f"  Domain: {result['domain']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Method: {result['method']}")


def test_work_history_enrichment():
    """Test work history enrichment and primary sector calculation."""
    print("\n" + "="*60)
    print("TEST 3: Work History Enrichment")
    print("="*60)
    
    sample_work_history = [
        {
            "company": "Axis Bank",
            "role": "Software Engineer",
            "start_date": "Jan 2020",
            "end_date": "Dec 2022",
            "is_current": 0,
            "description": "Developed banking applications"
        },
        {
            "company": "Infosys",
            "role": "Senior Software Engineer",
            "start_date": "Jan 2023",
            "end_date": "Present",
            "is_current": 1,
            "description": "Working on enterprise solutions"
        }
    ]
    
    # Enrich work history
    enriched = enrich_work_history_with_sectors(sample_work_history)
    
    print("\nEnriched Work History:")
    for i, job in enumerate(enriched, 1):
        print(f"\nJob {i}:")
        print(f"  Company: {job['company']}")
        print(f"  Role: {job['role']}")
        print(f"  Sector: {job.get('sector', 'N/A')}")
        print(f"  Domain: {job.get('domain', 'N/A')}")
    
    # Get primary sector
    sector_analysis = get_candidate_primary_sector(enriched)
    
    print("\n" + "-"*60)
    print("Candidate Sector Analysis:")
    print("-"*60)
    print(f"Primary Sector: {sector_analysis['primary_sector']}")
    print(f"Sector Experience: {sector_analysis['sector_experience']}")
    print(f"Sector Transitions: {sector_analysis['sector_transitions']}")
    print(f"Total Companies: {sector_analysis['total_companies']}")


def test_edge_cases():
    """Test edge cases."""
    print("\n" + "="*60)
    print("TEST 4: Edge Cases")
    print("="*60)
    
    test_cases = [
        "",
        "Unknown Company XYZ",
        "ABC Corp",
        "   ",
        "TCS India Pvt Ltd"
    ]
    
    for company in test_cases:
        result = identify_company_sector(company)
        print(f"\n'{company}':")
        print(f"  Sector: {result['sector']}")
        print(f"  Domain: {result['domain']}")
        print(f"  Confidence: {result['confidence']}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("COMPANY SECTOR IDENTIFICATION - TEST SUITE")
    print("="*60)
    
    try:
        test_predefined_companies()
        test_keyword_matching()
        test_work_history_enrichment()
        test_edge_cases()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
