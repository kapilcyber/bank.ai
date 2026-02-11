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
    get_candidate_primary_sector
)

async def backfill():
    print("Starting sector backfill for existing resumes...")
    async with AsyncSessionLocal() as session:
        # Fetch all resumes with their work history
        result = await session.execute(
            select(Resume).options(selectinload(Resume.work_history))
        )
        resumes = result.scalars().all()
        print(f"Checking {len(resumes)} resumes for sector updates...")
        
        updated_count = 0
        for resume in resumes:
            work_history = resume.work_history
            if not work_history:
                continue
                
            history_dicts = []
            updates_made = False
            
            # 1. Update individual experience entries
            for exp in work_history:
                if not exp.company:
                    continue
                
                # Identify sector/domain using the mapper service
                sector_result = identify_company_sector(exp.company)
                sector = sector_result.get('sector', 'Unknown')
                domain = sector_result.get('domain', 'Unknown')
                
                # Check if update is needed
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
            
            # 2. Update aggregated fields in parsed_data
            if history_dicts:
                # get_candidate_primary_sector returns a dict with all analysis
                analysis = get_candidate_primary_sector(history_dicts)
                
                primary = analysis.get('primary_sector')
                breakdown = analysis.get('sector_experience')
                transitions = analysis.get('sector_transitions')
                
                parsed = dict(resume.parsed_data or {})
                
                # Check if aggregate values changed
                if (parsed.get('primary_sector') != primary or 
                    parsed.get('sector_experience') != breakdown):
                    
                    parsed['primary_sector'] = primary
                    parsed['sector_experience'] = breakdown
                    parsed['sector_transitions'] = transitions
                    
                    resume.parsed_data = parsed
                    updates_made = True
            
            if updates_made:
                session.add(resume)
                updated_count += 1
        
        await session.commit()
        print(f"Backfill complete! Successfully updated {updated_count} resumes.")

if __name__ == "__main__":
    asyncio.run(backfill())
