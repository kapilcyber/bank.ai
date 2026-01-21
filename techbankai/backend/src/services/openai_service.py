"""OpenAI service for AI-powered parsing and matching."""
import json
from openai import AsyncOpenAI
from typing import Dict, List
from src.utils.logger import get_logger
from src.config.settings import settings

logger = get_logger(__name__)

# OpenAI Configuration from settings
OPENAI_API_KEY = settings.openai_api_key
OPENAI_MODEL = settings.openai_model
OPENAI_MAX_TOKENS = settings.openai_max_tokens

# Initialize OpenAI client lazily to avoid import-time errors
_client = None


def get_openai_client():
    """Get or create OpenAI client (lazy initialization)."""
    global _client
    if _client is None and OPENAI_API_KEY:
        try:
            _client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")
            _client = None
    return _client


async def parse_resume_with_gpt(resume_text: str) -> Dict:
    """
    Use GPT-4 to extract structured data from resume text.
    Returns: Structured resume data as dictionary matching ParsedResume schema.
    """
    client = get_openai_client()
    if not client:
        logger.error("OpenAI client not initialized - API key missing or invalid")
        raise ValueError("OpenAI API key not configured")
    
    try:
        system_prompt = """You are an expert resume parser and HR analyst. 
Extract structured information from resumes with high accuracy.
NEVER hallucinate or invent data. If information is not present, use "Not mentioned" for strings, 0.0 for numbers, or empty arrays.
Return data as valid JSON only, no additional text."""
        
        logger.info(f"Parsing resume. Text length: {len(resume_text)}")
        user_prompt = f"""Extract Resume Data (JSON only):
{resume_text[:4000]}

Fields:
"resume_candidate_name", 
"resume_contact_info" (email), 
"resume_phone" (phone number in any format - extract from contact section, header, or anywhere in resume),
"resume_role" (current or most recent job title/role),
"resume_location" (full location string like "City, Country" or "City, State, Country"),
"resume_address" (street address if available, otherwise empty string),
"resume_city" (city name extracted from location),
"resume_country" (country name extracted from location),
"resume_zip_code" (postal/zip code if available, otherwise empty string),
"resume_degree", 
"resume_university", 
"resume_experience" (float), 
"resume_technical_skills" (list), 
"resume_projects" (list), 
"resume_achievements" (list), 
"resume_certificates" (list), 
"all_skills" (list), 
"notice_period" (days), 
"ready_to_relocate" (bool),
"current_company" (extract from work_history where is_current = 1, or most recent company if no current job marked),
"work_history": [
  {{
    "company": "...",
    "role": "...",
    "location": "...",
    "start_date": "...",
    "end_date": "..." or "Present" or "Current",
    "is_current": 0 | 1,
    "description": "Brief summary of responsibilities and achievements in this role"
  }}
]

IMPORTANT EXTRACTION RULES:
- Extract phone number from anywhere in resume (header, contact section, etc.) - formats like +1-234-567-8900, (123) 456-7890, 123-456-7890, etc.
- For address: Extract street address, city, country, and zip code separately if available
- For current_company: Use the company name from the most recent work_history entry where is_current = 1, or the most recent company if no current job is explicitly marked
- Parse location string into separate city and country fields when possible
- If location is "City, Country", extract city and country separately
- If zip code is in location string (e.g., "New York, NY 10001"), extract it to resume_zip_code
"""
        
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=min(OPENAI_MAX_TOKENS, 4096),
            temperature=0.1 # High precision
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Normalize skills to lowercase and deduplicate
        if "resume_technical_skills" in result:
            result["resume_technical_skills"] = list(set([s.lower().strip() for s in result["resume_technical_skills"] if s]))
        if "all_skills" in result:
            result["all_skills"] = list(set([s.lower().strip() for s in result["all_skills"] if s]))
        
        # Extract current company from work_history if available
        work_history = result.get("work_history", [])
        if work_history and not result.get("current_company"):
            # Find current job or most recent job
            for job in work_history:
                if job.get("is_current") == 1:
                    result["current_company"] = job.get("company", "")
                    break
            # If no current job found, use most recent
            if not result.get("current_company") and work_history:
                result["current_company"] = work_history[0].get("company", "")
        
        # Parse location into city and country if not already extracted
        location = result.get("resume_location", "")
        if location and location != "Not mentioned":
            if not result.get("resume_city") and not result.get("resume_country"):
                # Try to split location string
                parts = [p.strip() for p in location.split(',')]
                if len(parts) >= 2:
                    result["resume_city"] = parts[0]
                    result["resume_country"] = parts[-1]
                elif len(parts) == 1:
                    result["resume_city"] = parts[0]
        
        # Ensure all required fields have defaults
        result.setdefault("resume_candidate_name", "Not mentioned")
        result.setdefault("resume_contact_info", "Not mentioned")
        result.setdefault("resume_phone", "")
        result.setdefault("resume_role", "Not mentioned")
        result.setdefault("resume_location", "Not mentioned")
        result.setdefault("resume_address", "")
        result.setdefault("resume_city", "")
        result.setdefault("resume_country", "")
        result.setdefault("resume_zip_code", "")
        result.setdefault("current_company", "")
        result.setdefault("resume_degree", "Not mentioned")
        result.setdefault("resume_university", "Not mentioned")
        result.setdefault("resume_experience", 0.0)
        result.setdefault("resume_technical_skills", [])
        result.setdefault("resume_projects", [])
        result.setdefault("resume_achievements", [])
        result.setdefault("resume_certificates", [])
        result.setdefault("all_skills", [])
        
        logger.info(f"Successfully parsed resume with GPT-4")
        return result
    
    except Exception as e:
        logger.error(f"GPT-4 resume parsing failed: {e}")
        raise


async def extract_jd_requirements(jd_text: str) -> Dict:
    """
    Use GPT-4 to analyze job description and extract requirements.
    Returns: Structured JD requirements.
    """
    client = get_openai_client()
    if not client:
        logger.error("OpenAI client not initialized - API key missing or invalid")
        raise ValueError("OpenAI API key not configured")
    
    try:
        system_prompt = """You are an enterprise-grade Job Description (JD) Decomposition Engine.

Your ONLY task is to analyze a Job Description (JD) and convert it into a
structured, weighted requirement model suitable for strict resume matching.

You MUST NOT:
- Score resumes
- Mention candidates
- Infer skills not stated or strongly implied
- Add explanations outside the JSON output

You MUST:
- Decompose the JD into EXACTLY the categories listed below
- Assign weights based on importance implied by the JD
- Ensure total weight = 100
- Return VALID JSON ONLY (no markdown, no commentary)

MANDATORY JD CATEGORIES:
1. Experience & Seniority
2. Core Technical Skills
3. Networking & Protocols
4. Security Technologies
5. Cloud & Architecture
6. Incident & Operations
7. Compliance & Governance
8. Certifications

RULES:
- Prefer explicit requirements over nice-to-haves
- If a category is weakly mentioned, assign a lower weight (minimum 5)
- Do NOT invent certifications or tools
- Seniority must be inferred from role title and responsibilities
- Use concise, normalized skill names (e.g., "NGFW", "IDS/IPS", "BGP")

return JSON in the following structure ONLY:

{
  "experience_seniority": {
    "required_years": <number>,
    "role_level": "<Engineer | Senior | Lead | Manager | Architect>",
    "weight": <number>
  },
  "core_technical_skills": {
    "items": [ "<skill>", "<skill>" ],
    "weight": <number>
  },
  "networking_protocols": {
    "items": [ "<protocol>", "<protocol>" ],
    "weight": <number>
  },
  "security_technologies": {
    "items": [ "<tool_or_tech>", "<tool_or_tech>" ],
    "weight": <number>
  },
  "cloud_architecture": {
    "items": [ "<cloud_or_architecture>" ],
    "weight": <number>
  },
  "incident_operations": {
    "items": [ "<incident_or_ops_requirement>" ],
    "weight": <number>
  },
  "compliance_governance": {
    "items": [ "<standard_or_framework>" ],
    "weight": <number>
  },
  "certifications": {
    "items": [ "<certification>" ],
    "weight": <number>
  }
}
"""
        
        user_prompt = f"""Analyze this job description:

{jd_text[:3500]}

Decompose into the strict JSON format required.
"""
        
        # Use a safe maximum for tokens
        max_tokens = min(OPENAI_MAX_TOKENS, 4096)
        
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=max_tokens,
            temperature=0.2 # Low temperature for consistency
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Backward compatibility mapping for `jd_analysis.py` which expects flat structure
        # We perform this mapping here so the rest of the app continues to work while we transition
        # Handle both new structured format and legacy flat format
        try:
            # Check if result is in new structured format
            if "experience_seniority" in result or "core_technical_skills" in result:
                flattened_result = {
                    "job_level": (result.get("experience_seniority") or {}).get("role_level", "Experienced"),
                    "min_experience_years": (result.get("experience_seniority") or {}).get("required_years") or 0,
                    "required_skills": (
                        (result.get("core_technical_skills", {}) or {}).get("items", []) + 
                        (result.get("networking_protocols", {}) or {}).get("items", []) +
                        (result.get("security_technologies", {}) or {}).get("items", []) +
                        (result.get("cloud_architecture", {}) or {}).get("items", [])
                    ),
                    "preferred_skills": result.get("preferred_skills", []),
                    "keywords": (
                        (result.get("compliance_governance", {}) or {}).get("items", []) +
                        (result.get("incident_operations", {}) or {}).get("items", [])
                    ),
                    # Store the full structured decomposition for the matcher
                    "structured_requirements": result,
                    "weights": {k: (v.get("weight", 0) if isinstance(v, dict) else 0) for k, v in result.items() if isinstance(v, dict)},
                    "education": result.get("education", ""),
                    "key_responsibilities": result.get("key_responsibilities", [])
                }
            else:
                # Legacy flat format - use as-is with defaults
                flattened_result = {
                    "job_level": result.get("job_level", "Experienced"),
                    "min_experience_years": result.get("min_experience_years", 0),
                    "required_skills": result.get("required_skills", []),
                    "preferred_skills": result.get("preferred_skills", []),
                    "keywords": result.get("keywords", []),
                    "education": result.get("education", ""),
                    "structured_requirements": result,
                    "weights": {},
                    "key_responsibilities": result.get("key_responsibilities", [])
                }
            
            logger.info(f"Successfully extracted JD requirements with GPT-4. Skills: {len(flattened_result.get('required_skills', []))}")
            return flattened_result
        except Exception as mapping_error:
            logger.error(f"Error mapping JD requirements structure: {mapping_error}. Raw result: {result}")
            # Fallback to basic structure
            return {
                "job_level": "Experienced",
                "min_experience_years": 0,
                "required_skills": result.get("required_skills", []),
                "preferred_skills": result.get("preferred_skills", []),
                "keywords": result.get("keywords", []),
                "education": result.get("education", ""),
                "structured_requirements": result,
                "weights": {},
                "key_responsibilities": result.get("key_responsibilities", [])
            }
    
    except json.JSONDecodeError as json_error:
        logger.error(f"Failed to parse OpenAI JSON response: {json_error}")
        logger.error(f"Response content: {response.choices[0].message.content if 'response' in locals() else 'No response'}")
        raise ValueError(f"Invalid JSON response from OpenAI: {str(json_error)}")
    except Exception as e:
        logger.error(f"GPT-4 JD extraction failed: {e}", exc_info=True)
        raise


async def calculate_intelligent_match(resume_data: Dict, jd_requirements: Dict) -> Dict:
    """
    Use GPT-4 to perform intelligent semantic matching.
    Returns: Match score and detailed analysis.
    """
    client = get_openai_client()
    if not client:
        logger.error("OpenAI client not initialized - API key missing or invalid")
        raise ValueError("OpenAI API key not configured")
    
    try:
        system_prompt = """You are an enterprise-grade Resume Analysis Engine.

Your task is to provide QUALITATIVE JUDGMENTS ONLY for each JD category.

DO NOT:
- Return numeric scores
- Return percentages
- Calculate final scores
- Apply penalties or bonuses

DO:
- Assess match level (HIGH, MEDIUM, LOW, NO)
- Assess ownership level (LED, OWNED, CONTRIBUTED, ASSISTED, NONE)
- Provide evidence from resume
- Indicate if experience is recent (last 5 years)

MATCH LEVEL DEFINITIONS:
- HIGH: Candidate has deep, proven expertise with strong evidence
- MEDIUM: Candidate has relevant experience but limited depth
- LOW: Candidate has minimal or tangential experience
- NO: No evidence of this skill/experience

OWNERSHIP LEVEL DEFINITIONS:
- LED: Led teams, projects, or initiatives (leadership verbs: led, managed, directed, architected)
- OWNED: Owned outcomes, systems, or processes (ownership verbs: owned, designed, built, implemented)
- CONTRIBUTED: Contributed to team efforts (contribution verbs: contributed, developed, worked on)
- ASSISTED: Assisted or supported (support verbs: assisted, supported, helped)
- NONE: No evidence

STRICT RULES:
- Prioritize recent experience (last 5 years)
- Look for ownership verbs over participation verbs
- Require explicit evidence, not assumptions
- Be brutally honest

OUTPUT FORMAT (JSON ONLY):
{
  "experience_seniority": {
    "match_level": "HIGH|MEDIUM|LOW|NO",
    "ownership": "LED|OWNED|CONTRIBUTED|ASSISTED|NONE",
    "evidence": "Specific evidence from resume",
    "recent": true|false
  },
  "core_technical_skills": {
    "match_level": "HIGH|MEDIUM|LOW|NO",
    "ownership": "LED|OWNED|CONTRIBUTED|ASSISTED|NONE",
    "evidence": "Specific skills mentioned"
  },
  "networking_protocols": {
    "match_level": "HIGH|MEDIUM|LOW|NO",
    "ownership": "LED|OWNED|CONTRIBUTED|ASSISTED|NONE",
    "evidence": "Specific protocols/technologies"
  },
  "security_technologies": {
    "match_level": "HIGH|MEDIUM|LOW|NO",
    "ownership": "LED|OWNED|CONTRIBUTED|ASSISTED|NONE",
    "evidence": "Specific security tools/technologies"
  },
  "cloud_architecture": {
    "match_level": "HIGH|MEDIUM|LOW|NO",
    "ownership": "LED|OWNED|CONTRIBUTED|ASSISTED|NONE",
    "evidence": "Specific cloud platforms/architectures"
  },
  "incident_operations": {
    "match_level": "HIGH|MEDIUM|LOW|NO",
    "ownership": "LED|OWNED|CONTRIBUTED|ASSISTED|NONE",
    "evidence": "Incident handling experience"
  },
  "compliance_governance": {
    "match_level": "HIGH|MEDIUM|LOW|NO",
    "ownership": "LED|OWNED|CONTRIBUTED|ASSISTED|NONE",
    "evidence": "Compliance standards/frameworks"
  },
  "certifications": {
    "match_level": "HIGH|MEDIUM|LOW|NO",
    "ownership": "OWNED|NONE",
    "evidence": "Certifications held"
  }
}
"""
        
        # Prepare structured inputs for the prompt
        structured_jd = jd_requirements.get('structured_requirements', jd_requirements)
        
        # Handle certifications - can be strings, dictionaries, lists, or nested structures
        certifications = resume_data.get('certifications', [])
        cert_strs = []
        
        # First, flatten any nested lists
        flat_certs = []
        for item in certifications:
            if item is None:
                continue
            if isinstance(item, list):
                flat_certs.extend([c for c in item if c is not None])
            else:
                flat_certs.append(item)
        
        # Now process each cert
        for cert in flat_certs:
            if cert is None:
                continue
            try:
                if isinstance(cert, dict):
                    # Extract name or use string representation
                    # Handle nested dicts - ensure we always get a string
                    name = cert.get('name') or cert.get('certification') or cert.get('cert_name')
                    if name:
                        # If name is still a dict or list, convert to string
                        if isinstance(name, dict):
                            cert_str = json.dumps(name)
                        elif isinstance(name, list):
                            cert_str = ', '.join(str(c) for c in name if c is not None)
                        else:
                            cert_str = str(name) if not isinstance(name, str) else name
                    else:
                        # Fallback to JSON string representation of entire dict
                        cert_str = json.dumps(cert)
                elif isinstance(cert, str):
                    cert_str = cert
                elif isinstance(cert, list):
                    # If cert is a list, join its string representations
                    cert_str = ', '.join(str(c) for c in cert if c is not None)
                else:
                    # Convert anything else to string
                    cert_str = str(cert)
                
                # Final safety check - ensure it's a string and not empty before appending
                if isinstance(cert_str, str) and cert_str.strip():
                    cert_strs.append(cert_str.strip())
            except Exception as cert_error:
                # If anything goes wrong, just skip this cert
                logger.warning(f"Error processing certification {cert}: {cert_error}")
                continue
        
        # Final safety check - ensure all items are strings before joining
        cert_strs = [str(c).strip() for c in cert_strs if c and str(c).strip()]
        
        # Handle skills - ensure all are strings
        skills = resume_data.get('skills', [])[:20]
        skill_strs = []
        for skill in skills:
            if skill is None:
                continue
            try:
                if isinstance(skill, (dict, list)):
                    skill_str = json.dumps(skill) if isinstance(skill, dict) else ', '.join(str(s) for s in skill if s is not None)
                else:
                    skill_str = str(skill) if not isinstance(skill, str) else skill
                if skill_str.strip():
                    skill_strs.append(skill_str.strip())
            except Exception:
                # Skip problematic skills
                continue
        
        user_prompt = f"""ANALYZE THIS RESUME AGAINST JD REQUIREMENTS:

[JD REQUIREMENTS BY CATEGORY]
{json.dumps(structured_jd, indent=2)}

[CANDIDATE RESUME]
Name: {resume_data.get('resume_candidate_name', 'Unknown')}
Current Role: {resume_data.get('role', 'N/A')}
Total Experience: {resume_data.get('experience_years', 0)} years
Skills: {', '.join(skill_strs) if skill_strs else 'None'}
Certifications: {', '.join(cert_strs) if cert_strs else 'None'}

Resume Summary:
{resume_data.get('summary', '')[:2000]}

Resume Text (Recent Experience):
{resume_data.get('raw_text', '')[:3500]}

For EACH JD category above, provide:
1. Match level (HIGH/MEDIUM/LOW/NO)
2. Ownership level (LED/OWNED/CONTRIBUTED/ASSISTED/NONE)
3. Specific evidence from resume
4. Whether experience is recent (last 5 years)

Return ONLY the JSON structure specified in the system prompt.
"""
        
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=min(OPENAI_MAX_TOKENS, 4096),
            temperature=0.1 # Very low temperature for deterministic scoring
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Successfully calculated intelligent match with GPT-4")
        return result
    
    except Exception as e:
        logger.error(f"GPT-4 matching failed: {e}")
        raise
