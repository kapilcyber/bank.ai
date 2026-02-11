"""Company sector mapping service."""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Cache for company database and sector mappings
_company_database = None
_sector_cache = {}


def load_company_database() -> Dict:
    """Load company-to-sector database from JSON file."""
    global _company_database
    
    if _company_database is not None:
        return _company_database
    
    try:
        db_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'data',
            'company_sector_database.json'
        )
        
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Flatten the database for easier lookup
        _company_database = {}
        for sector_group, companies in data.items():
            for company_name, company_info in companies.items():
                # Store with normalized key (lowercase, stripped)
                normalized_key = company_name.lower().strip()
                _company_database[normalized_key] = company_info
        
        logger.info(f"Loaded {len(_company_database)} companies from sector database")
        return _company_database
    
    except Exception as e:
        logger.error(f"Failed to load company database: {e}")
        return {}


def normalize_company_name(company_name: str) -> str:
    """Normalize company name for matching."""
    if not company_name:
        return ""
    
    # Remove common suffixes
    suffixes = [
        'ltd', 'limited', 'pvt', 'private', 'inc', 'incorporated',
        'corp', 'corporation', 'llc', 'llp', 'co', 'company'
    ]
    
    normalized = company_name.lower().strip()
    
    # Remove punctuation
    normalized = normalized.replace('.', '').replace(',', '')
    
    # Remove suffixes
    for suffix in suffixes:
        if normalized.endswith(f' {suffix}'):
            normalized = normalized[:-len(suffix)-1].strip()
    
    return normalized


def identify_sector_by_keywords(company_name: str) -> Optional[Dict]:
    """Identify sector using keyword-based matching."""
    if not company_name:
        return None
    
    company_lower = company_name.lower()
    
    # Keyword patterns for different sectors
    keyword_patterns = {
        'BFSI': {
            'keywords': ['bank', 'banking', 'finance', 'financial', 'insurance', 
                        'securities', 'mutual fund', 'asset management', 'fintech',
                        'payments', 'lending', 'credit'],
            'domain': 'Financial Services'
        },
        'IT Services': {
            'keywords': ['technologies', 'technology', 'software', 'systems', 
                        'solutions', 'infotech', 'consulting', 'digital'],
            'domain': 'Software & IT'
        },
        'Healthcare': {
            'keywords': ['hospital', 'healthcare', 'medical', 'pharma', 
                        'pharmaceutical', 'clinic', 'health', 'diagnostics'],
            'domain': 'Healthcare Services'
        },
        'E-commerce': {
            'keywords': ['ecommerce', 'e-commerce', 'marketplace', 'retail online'],
            'domain': 'Online Retail'
        },
        'Manufacturing': {
            'keywords': ['manufacturing', 'industries', 'motors', 'steel', 
                        'engineering', 'auto', 'automotive'],
            'domain': 'Manufacturing'
        },
        'Telecom': {
            'keywords': ['telecom', 'telecommunications', 'mobile', 'network'],
            'domain': 'Telecommunications'
        },
        'Education': {
            'keywords': ['education', 'learning', 'academy', 'institute', 
                        'university', 'college', 'school'],
            'domain': 'Education'
        },
        'Consulting': {
            'keywords': ['consulting', 'consultancy', 'advisory', 'advisors'],
            'domain': 'Consulting Services'
        }
    }
    
    # Check each sector's keywords
    for sector, info in keyword_patterns.items():
        for keyword in info['keywords']:
            if keyword in company_lower:
                return {
                    'sector': sector,
                    'domain': info['domain'],
                    'confidence': 'medium',
                    'method': 'keyword'
                }
    
    return None


# Cache file path
CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'sector_ai_cache.json')

def load_ai_cache():
    """Load AI-identified sectors from cache file."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load sector AI cache: {e}")
    return {}

def save_ai_cache(cache_data: Dict):
    """Save AI-identified sectors to cache file."""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save sector AI cache: {e}")

# Initialize cache with persistent data
_sector_cache = load_ai_cache()


def identify_company_sector(company_name: str, use_ai: bool = False) -> Dict:
    """
    Identify sector and domain for a company.
    
    Args:
        company_name: Name of the company
        use_ai: Whether to use AI for unknown companies (default: False)
    
    Returns:
        Dict with sector, domain, confidence, and method
    """
    if not company_name or company_name.strip() == "":
        return {
            'sector': 'Unknown',
            'domain': 'Unknown',
            'confidence': 'none',
            'method': 'none'
        }
    
    # Check cache first (includes persistent AI cache)
    cache_key = normalize_company_name(company_name)
    if cache_key in _sector_cache:
        return _sector_cache[cache_key]
    
    # Step 1: Try exact match in database
    db = load_company_database()
    normalized = normalize_company_name(company_name)
    
    if normalized in db:
        result = {
            **db[normalized],
            'confidence': 'high',
            'method': 'database'
        }
        _sector_cache[cache_key] = result
        return result
    
    # Step 2: Try partial match (for variations like "TCS India" vs "TCS")
    for db_company, info in db.items():
        if db_company in normalized or normalized in db_company:
            result = {
                **info,
                'confidence': 'high',
                'method': 'database_partial'
            }
            _sector_cache[cache_key] = result
            return result
    
    # Step 3: Try keyword-based matching
    keyword_result = identify_sector_by_keywords(company_name)
    if keyword_result:
        _sector_cache[cache_key] = keyword_result
        return keyword_result
    
    # Step 4: AI-powered identification (optional, requires OpenAI)
    if use_ai:
        try:
            from src.services.openai_service import identify_company_sector_with_gpt
            import asyncio
            
            # Run async function
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, create task
                # Note: This returns a coro, we need to await it or run it.
                # Since this function is sync, we can't await.
                # We should use run_until_complete if loop is not running, 
                # but if loop IS running (e.g. inside FastAPI), we can't block it.
                # Refactor: Make identify_company_sector async? No, existing code depends on sync.
                # Solution: If loop is running, we cannot easily run async code synchronously.
                # Forcing use_ai=True in sync context within async loop is tricky.
                # However, for backfill script (running loop), we can call the async version directly.
                # For resume_parser (async), we should use an async version.
                
                # Check if we can use a separate thread or just skip for now?
                # Best approach: Add async_identify_company_sector.
                pass
            else:
                 ai_result = loop.run_until_complete(
                    identify_company_sector_with_gpt(company_name)
                )
                 if ai_result and ai_result.get('sector') != 'Unknown':
                    _sector_cache[cache_key] = ai_result
                    save_ai_cache(_sector_cache)
                    return ai_result

        except Exception as e:
            logger.warning(f"AI sector identification failed for {company_name}: {e}")
            # Try to handle the 'RuntimeError: This event loop is already running'
            # We will ignore AI if we can't run it synchronously.
    
    # Step 5: Return unknown
    result = {
        'sector': 'Unknown',
        'domain': 'Unknown',
        'confidence': 'none',
        'method': 'none'
    }
    # Don't cache 'Unknown' permanently to allow future AI checks
    # _sector_cache[cache_key] = result 
    return result


def get_candidate_primary_sector(work_history: List[Dict]) -> Dict:
    """
    Analyze work history to determine candidate's primary sector.
    
    Args:
        work_history: List of work experience entries
    
    Returns:
        Dict with primary_sector, sector_experience, and sector_transitions
    """
    if not work_history:
        return {
            'primary_sector': 'Unknown',
            'sector_experience': {},
            'sector_transitions': [],
            'total_companies': 0
        }
    
    sector_years = {}
    sector_sequence = []
    
    for job in work_history:
        company = job.get('company', '')
        sector_info = identify_company_sector(company)
        sector = sector_info.get('sector', 'Unknown')
        
        # Calculate years for this job
        years = calculate_job_duration(job)
        
        # Accumulate sector experience
        if sector not in sector_years:
            sector_years[sector] = 0.0
        sector_years[sector] += years
        
        # Track sector sequence
        if not sector_sequence or sector_sequence[-1] != sector:
            sector_sequence.append(sector)
    
    # Determine primary sector (most years of experience)
    if sector_years:
        primary_sector = max(sector_years.items(), key=lambda x: x[1])[0]
    else:
        primary_sector = 'Unknown'
    
    # Identify sector transitions
    transitions = []
    for i in range(len(sector_sequence) - 1):
        if sector_sequence[i] != sector_sequence[i + 1]:
            transition = f"{sector_sequence[i]} → {sector_sequence[i + 1]}"
            if transition not in transitions:
                transitions.append(transition)
    
    return {
        'primary_sector': primary_sector,
        'sector_experience': sector_years,
        'sector_transitions': transitions,
        'total_companies': len(work_history)
    }


def calculate_job_duration(job: Dict) -> float:
    """
    Calculate duration of a job in years.
    
    Args:
        job: Work experience entry with start_date and end_date
    
    Returns:
        Duration in years (float)
    """
    from datetime import datetime
    import re
    
    start_date = job.get('start_date', '')
    end_date = job.get('end_date', '')
    
    if not start_date:
        return 0.0
    
    # Handle "Present" or "Current"
    if end_date.lower() in ['present', 'current', '']:
        end_date = datetime.now().strftime('%b %Y')
    
    try:
        # Parse dates (handle various formats)
        start = parse_date_string(start_date)
        end = parse_date_string(end_date)
        
        if start and end:
            delta = end - start
            years = delta.days / 365.25
            return round(years, 1)
    except Exception as e:
        logger.debug(f"Could not calculate duration for {start_date} to {end_date}: {e}")
    
    # Fallback: estimate 2 years per job if dates can't be parsed
    return 2.0


def parse_date_string(date_str: str) -> Optional[datetime]:
    """Parse date string in various formats."""
    from datetime import datetime
    
    if not date_str:
        return None
    
    # Common date formats
    formats = [
        '%b %Y',      # Jan 2020
        '%B %Y',      # January 2020
        '%m/%Y',      # 01/2020
        '%Y-%m',      # 2020-01
        '%Y',         # 2020
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    return None


async def identify_company_sector_async(company_name: str, use_ai: bool = True) -> Dict:
    """
    Async version of identify_company_sector.
    Identify sector and domain for a company, using AI if needed.
    
    Args:
        company_name: Name of the company
        use_ai: Whether to use AI for unknown companies (default: True)
    
    Returns:
        Dict with sector, domain, confidence, and method
    """
    if not company_name or company_name.strip() == "":
        return {
            'sector': 'Unknown',
            'domain': 'Unknown',
            'confidence': 'none',
            'method': 'none'
        }
    
    # Check cache first (includes persistent AI cache)
    cache_key = normalize_company_name(company_name)
    if cache_key in _sector_cache:
        return _sector_cache[cache_key]
    
    # Step 1: Try exact match in database
    db = load_company_database()
    normalized = normalize_company_name(company_name)
    
    if normalized in db:
        result = {
            **db[normalized],
            'confidence': 'high',
            'method': 'database'
        }
        _sector_cache[cache_key] = result
        return result
    
    # Step 2: Partial match
    for db_company, info in db.items():
        if db_company in normalized or normalized in db_company:
            result = {
                **info,
                'confidence': 'high',
                'method': 'database_partial'
            }
            _sector_cache[cache_key] = result
            return result
    
    # Step 3: Keyword match
    keyword_result = identify_sector_by_keywords(company_name)
    if keyword_result:
        _sector_cache[cache_key] = keyword_result
        return keyword_result
    
    # Step 4: AI identification (Async)
    if use_ai:
        try:
            from src.services.openai_service import identify_company_sector_with_gpt
            
            # Since we are async, we can await directly
            ai_result = await identify_company_sector_with_gpt(company_name)
            
            if ai_result and ai_result.get('sector') != 'Unknown':
                _sector_cache[cache_key] = ai_result
                save_ai_cache(_sector_cache)
                return ai_result
        except Exception as e:
            logger.warning(f"Async AI sector identification failed for {company_name}: {e}")
    
    # Step 5: Unknown
    result = {
        'sector': 'Unknown',
        'domain': 'Unknown',
        'confidence': 'none',
        'method': 'none'
    }
    # Don't cache unknown permanently
    return result


async def enrich_work_history_with_sectors(work_history: List[Dict]) -> List[Dict]:
    """
    Enrich work history entries with sector and domain information (async).
    
    Args:
        work_history: List of work experience entries
    
    Returns:
        Enriched work history with sector and domain fields
    """
    enriched = []
    
    for job in work_history:
        company = job.get('company', '')
        # Use async identification with AI enabled by default
        sector_info = await identify_company_sector_async(company, use_ai=True)
        
        enriched_job = {
            **job,
            'sector': sector_info.get('sector', 'Unknown'),
            'domain': sector_info.get('domain', 'Unknown'),
            'sector_confidence': sector_info.get('confidence', 'none')
        }
        enriched.append(enriched_job)
    
    return enriched
