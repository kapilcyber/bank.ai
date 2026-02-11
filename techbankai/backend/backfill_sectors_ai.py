import asyncio
import sys
import os
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Add src to python path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models.resume import Resume
from src.config.database import AsyncSessionLocal
from src.services.company_sector_mapper import (
    identify_company_sector, 
    get_candidate_primary_sector,
    _sector_cache,
    save_ai_cache,
    normalize_company_name
)
from src.services.openai_service import identify_company_sector_with_gpt

async def backfill_ai():
    print("Starting AI-powered sector identification...")
    
    # Track unique companies to process to avoid redundant API calls
    unique_companies = set()
    
    async with AsyncSessionLocal() as session:
        # Load resumes
        result = await session.execute(select(Resume).options(selectinload(Resume.work_history)))
        resumes = result.scalars().all()
        
        # 1. Collect unknown companies
        for resume in resumes:
            for exp in (resume.work_history or []):
                if not exp.company: continue
                
                # Check current sector
                # We can re-check using identify_company_sector(use_ai=False) to see if it resolves via static DB
                res = identify_company_sector(exp.company, use_ai=False)
                if res['sector'] == 'Unknown':
                    unique_companies.add(exp.company)
        
        print(f"Found {len(unique_companies)} unique companies with Unknown sector. Processing with OpenAI...")
        
        # 2. Process with OpenAI
        processed_count = 0
        for company in unique_companies:
            # Check cache again case normalized key matches something already processed
            normalized = normalize_company_name(company)
            if normalized in _sector_cache and _sector_cache[normalized]['sector'] != 'Unknown':
                continue
            
            print(f"Identifying: {company}...", end=" ", flush=True)
            try:
                ai_result = await identify_company_sector_with_gpt(company)
                if ai_result and ai_result.get('sector') != 'Unknown':
                    _sector_cache[normalized] = ai_result
                    print(f"-> {ai_result['sector']}")
                else:
                    print(f"-> Failed/Unknown")
                    
                processed_count += 1
                if processed_count % 5 == 0:
                    save_ai_cache(_sector_cache) # Periodic save
            except Exception as e:
                print(f"Error: {e}")
        
        # Final save
        save_ai_cache(_sector_cache)
        print("\nAI processing complete. Updating database records with new findings...")
        
        # 3. Update DB records
        updated_count = 0
        for resume in resumes:
            work_history = resume.work_history
            if not work_history: continue
            
            history_dicts = []
            updates_made = False
            
            for exp in work_history:
                if not exp.company: continue
                
                # identify_company_sector will now hit the populated _sector_cache
                res = identify_company_sector(exp.company, use_ai=False) 
                sector = res.get('sector', 'Unknown')
                domain = res.get('domain', 'Unknown')
                
                if exp.sector != sector or exp.domain != domain:
                    exp.sector = sector
                    exp.domain = domain
                    updates_made = True
                
                history_dicts.append({
                    'company': exp.company,
                    'sector': sector,
                    'domain': domain,
                    'start_date': exp.start_date,
                    'end_date': exp.end_date,
                    'is_current': exp.is_current
                })
            
            if history_dicts:
                # Re-calculate candidate analysis based on upgraded sectors
                analysis = get_candidate_primary_sector(history_dicts)
                parsed = dict(resume.parsed_data or {})
                
                if (parsed.get('primary_sector') != analysis.get('primary_sector') or 
                    parsed.get('sector_experience') != analysis.get('sector_experience')):
                    
                    parsed['primary_sector'] = analysis.get('primary_sector')
                    parsed['sector_experience'] = analysis.get('sector_experience')
                    parsed['sector_transitions'] = analysis.get('sector_transitions')
                    resume.parsed_data = parsed
                    updates_made = True
            
            if updates_made:
                session.add(resume)
                updated_count += 1
        
        await session.commit()
        print(f"Database update complete! {updated_count} resumes updated with AI-enriched sector data.")

if __name__ == "__main__":
    asyncio.run(backfill_ai())
