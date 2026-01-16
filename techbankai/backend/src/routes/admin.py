from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from datetime import datetime, timedelta
from src.models.resume import Resume
from src.models.jd_analysis import JDAnalysis, MatchResult
from src.models.user_db import User
from src.config.database import get_postgres_db
from src.middleware.auth_middleware import get_admin_user
from src.utils.logger import get_logger
from src.utils.user_type_mapper import normalize_user_type, get_user_type_from_source_type
from src.utils.response_formatter import format_resume_response

logger = get_logger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/stats")
async def get_dashboard_stats(
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Get dashboard statistics with breakdown by user type and upload trends (Admin only)"""
    try:
        # Get PostgreSQL stats (including users)
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar()
        
        total_resumes_result = await db.execute(select(func.count(Resume.id)))
        total_resumes = total_resumes_result.scalar()
        
        total_jd_analyses_result = await db.execute(select(func.count(JDAnalysis.id)))
        total_jd_analyses = total_jd_analyses_result.scalar()
        
        total_matches_result = await db.execute(select(func.count(MatchResult.id)))
        total_matches = total_matches_result.scalar()
        
        # Get all resumes with formatted responses and prefetch relationships
        from sqlalchemy.orm import selectinload
        all_resumes_query = select(Resume).options(
            selectinload(Resume.work_history),
            selectinload(Resume.certificates)
        ).order_by(Resume.uploaded_at.desc())
        all_resumes_result = await db.execute(all_resumes_query)
        all_resumes = all_resumes_result.scalars().all()

        # Initialize trend data structure
        target_user_types = ['Company Employee', 'Freelancer', 'Guest User']
        
        # Helper to get normalized date/month/quarter
        def get_trend_keys(dt):
            year = dt.year
            month = dt.month
            quarter = (month - 1) // 3 + 1
            return {
                'day': dt.date().isoformat(),
                'month': f"{year}-{month:02d}",
                'quarter': f"{year}-Q{quarter}"
            }

        trends = {
            'day': {},
            'month': {},
            'quarter': {}
        }

        # Last 365 days for comprehensive trends
        one_year_ago = datetime.utcnow() - timedelta(days=365)

        user_type_counts = {ut: 0 for ut in target_user_types}
        user_type_skills = {ut: {} for ut in target_user_types}
        skill_count = {}
        experience_counts = {} # Bins: 0, 1, 2, 3...
        state_distribution = {} # Maharashtra, Karnataka, etc.
        role_candidates = {} # 'Software Engineer': [{'name': '...', 'exp': ...}, ...]

        # Indian State Mapping for normalization
        STATE_MAPPING = {
            'maharashtra': 'Maharashtra', 'mumbai': 'Maharashtra', 'pune': 'Maharashtra', 'nagpur': 'Maharashtra',
            'karnataka': 'Karnataka', 'bangalore': 'Karnataka', 'bengaluru': 'Karnataka', 'mysore': 'Karnataka',
            'delhi': 'Delhi', 'noida': 'Uttar Pradesh', 'gurgaon': 'Haryana', 'gurugram': 'Haryana',
            'tamil nadu': 'Tamil Nadu', 'chennai': 'Tamil Nadu', 'coimbatore': 'Tamil Nadu',
            'telangana': 'Telangana', 'hyderabad': 'Telangana',
            'west bengal': 'West Bengal', 'kolkata': 'West Bengal',
            'gujarat': 'Gujarat', 'ahmedabad': 'Gujarat', 'surat': 'Gujarat', 'vadodara': 'Gujarat',
            'rajasthan': 'Rajasthan', 'jaipur': 'Rajasthan', 'udaipur': 'Rajasthan',
            'punjab': 'Punjab', 'chandigarh': 'Chandigarh', 'amritsar': 'Punjab',
            'haryana': 'Haryana',
            'uttar pradesh': 'Uttar Pradesh', 'lucknow': 'Uttar Pradesh', 'kanpur': 'Uttar Pradesh',
            'madhya pradesh': 'Madhya Pradesh', 'indore': 'Madhya Pradesh', 'bhopal': 'Madhya Pradesh',
            'kerala': 'Kerala', 'kochi': 'Kerala', 'thiruvananthapuram': 'Kerala',
            'andhra pradesh': 'Andhra Pradesh', 'visakhapatnam': 'Andhra Pradesh',
            'bihar': 'Bihar', 'patna': 'Bihar',
            'odisha': 'Odisha', 'bhubaneswar': 'Odisha',
            'assam': 'Assam', 'guwahati': 'Assam',
            'chhattisgarh': 'Chhattisgarh', 'raipur': 'Chhattisgarh',
            'jharkhand': 'Jharkhand', 'ranchi': 'Jharkhand',
            'uttarakhand': 'Uttarakhand', 'dehradun': 'Uttarakhand',
            'himachal pradesh': 'Himachal Pradesh'
        }

        for resume in all_resumes:
            # Normalize user type
            meta = resume.meta_data or {}
            user_type = normalize_user_type(meta.get('user_type') or get_user_type_from_source_type(resume.source_type))
            
            # Global and Type-based counts/skills (for existing dashboard cards)
            if user_type in target_user_types:
                user_type_counts[user_type] += 1
                
                # Robust skill extraction
                skills_list = resume.skills or []
                if not skills_list and resume.parsed_data:
                     # fallback to parsed data
                     skills_list = resume.parsed_data.get('resume_technical_skills', []) or resume.parsed_data.get('all_skills', [])

                if skills_list:
                    for skill in skills_list:
                        # Normalize skill
                        skill = skill.strip()
                        if not skill: continue
                        
                        # Add to user type breakdown
                        user_type_skills[user_type][skill] = user_type_skills[user_type].get(skill, 0) + 1
                        
                        # Add to global count (regardless of who uploaded it)
                        skill_count[skill] = skill_count.get(skill, 0) + 1

            # Populate Experience Distribution
            exp = float(resume.experience_years or 0)
            exp_bin = int(exp) # Round down to nearest year
            experience_counts[exp_bin] = experience_counts.get(exp_bin, 0) + 1

            # Populate Trends
            if resume.uploaded_at >= one_year_ago:
                keys = get_trend_keys(resume.uploaded_at)
                for period in ['day', 'month', 'quarter']:
                    key = keys[period]
                    if key not in trends[period]:
                        trends[period][key] = {ut: 0 for ut in target_user_types}
                        trends[period][key]['name'] = key
                    
                    if user_type in target_user_types:
                        trends[period][key][user_type] += 1
            
            # Map location to Indian State
            # Safe extraction: Source Metadata (Form Data) > Parsed Data
            loc_str = ""
            if resume.source_metadata and 'form_data' in resume.source_metadata:
                loc_str = resume.source_metadata['form_data'].get('location') or ""
            
            if not loc_str and resume.parsed_data:
                loc_str = resume.parsed_data.get('resume_location') or resume.parsed_data.get('location') or ""
            
            loc = str(loc_str).lower()
            found_state = None
            for key, state in STATE_MAPPING.items():
                if key in loc:
                    found_state = state
                    break
            
            if found_state:
                state_distribution[found_state] = state_distribution.get(found_state, 0) + 1
            
            # Map Roles for Circle Packing
            role_str = ""
            if resume.source_metadata and 'form_data' in resume.source_metadata:
                role_str = resume.source_metadata['form_data'].get('role') or ""
            
            if not role_str and resume.parsed_data:
                role_str = resume.parsed_data.get('resume_role') or resume.parsed_data.get('role') or ""
            
            if role_str and role_str != "Not mentioned":
                # Basic normalization: title case
                norm_role = role_str.strip().title()
                if norm_role not in role_candidates:
                    role_candidates[norm_role] = []
                
                # Correctly extract name for the tooltip preview
                cand_name = None
                if resume.source_metadata and 'form_data' in resume.source_metadata:
                    cand_name = resume.source_metadata['form_data'].get('fullName') or resume.source_metadata['form_data'].get('name')
                
                if not cand_name and resume.parsed_data:
                    p = resume.parsed_data
                    cand_name = p.get('resume_candidate_name') or p.get('candidate_name') or p.get('name') or p.get('fullName')
                
                if not cand_name or str(cand_name).lower() == "not mentioned":
                    cand_name = "Anonymous"

                role_candidates[norm_role].append({
                    'name': str(cand_name),
                    'exp': float(resume.experience_years or 0)
                })

        # Format trends for Recharts (sorted lists)
        formatted_trends = {
            p: sorted(trends[p].values(), key=lambda x: x['name'])
            for p in ['day', 'month', 'quarter']
        }
        
        # Only take last 30 days for 'day' to avoid bloated response, but keep full year for others
        formatted_trends['day'] = formatted_trends['day'][-30:]

        top_skills = sorted(skill_count.items(), key=lambda x: x[1], reverse=True)[:10]
        top_skills_by_user_type = {
            ut: sorted(skills_dict.items(), key=lambda x: x[1], reverse=True)[:5]
            for ut, skills_dict in user_type_skills.items()
        }

        # Get all JD analyses
        recent_jd_query = select(JDAnalysis).order_by(JDAnalysis.submitted_at.desc())
        recent_jd_result = await db.execute(recent_jd_query)
        recent_jd = recent_jd_result.scalars().all()

        return {
            'total_users': total_users,
            'total_records': total_resumes, # Renamed for frontend consistency
            'total_jd_analyses': total_jd_analyses,
            'total_matches': total_matches,
            'departmentDistribution': user_type_counts, # Keep name for backwards compatibility during transition
            'user_type_breakdown': user_type_counts,
            'top_skills': [{'skill': skill, 'count': count} for skill, count in top_skills],
            'top_skills_by_user_type': {
                ut: [{'skill': skill, 'count': count} for skill, count in skills_list]
                for ut, skills_list in top_skills_by_user_type.items()
            },
            'experience_distribution': sorted(
                [{'exp': exp, 'count': experience_counts.get(exp, 0)} for exp in range(0, (max(experience_counts.keys()) if experience_counts else 0) + 1)],
                key=lambda x: x['exp']
            ),
            'location_distribution': [{'state': s, 'count': c} for s, c in state_distribution.items()],
            'role_distribution': sorted([
                {
                    'role': r, 
                    'count': len(cands), 
                    'candidates': sorted(cands, key=lambda x: x['exp'], reverse=True)
                } 
                for r, cands in role_candidates.items()
            ], key=lambda x: x['count'], reverse=True),
            'trends': formatted_trends,
            'recentResumes': [ # Renamed for frontend consistency
                format_resume_response(r)
                for r in all_resumes[:50] # Limit to latest 50 for performance
            ],
            'recent_jd_analyses': [
                {
                    'job_id': jd.job_id,
                    'filename': jd.jd_filename,
                    'submitted_at': jd.submitted_at.isoformat() if jd.submitted_at else None
                }
                for jd in recent_jd
            ],
            'departments': target_user_types
        }
    
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """List all users (Admin only)"""
    try:
        total_result = await db.execute(select(func.count(User.id)))
        total = total_result.scalar()
        
        users_query = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        users_result = await db.execute(users_query)
        users = users_result.scalars().all()
        
        return {
            'total': total,
            'skip': skip,
            'limit': limit,
            'users': [
                {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'mode': user.mode or 'user',
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }
                for user in users
            ]
        }
    
    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Delete user (Admin only)"""
    try:
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        await db.execute(delete(User).where(User.id == user_id))
        await db.commit()
        
        logger.info(f"Deleted user: {user_id}")
        return {"message": "User deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/resumes/bulk")
async def bulk_delete_resumes(
    resume_ids: list[int],
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Bulk delete resumes (Admin only)"""
    try:
        deleted_count = 0
        for resume_id in resume_ids:
            query = select(Resume).where(Resume.id == resume_id)
            result = await db.execute(query)
            resume = result.scalar_one_or_none()
            if resume:
                await db.execute(delete(Resume).where(Resume.id == resume_id))
                deleted_count += 1
        
        await db.commit()
        
        logger.info(f"Bulk deleted {deleted_count} resumes")
        return {
            'message': f'Successfully deleted {deleted_count} resumes',
            'deleted_count': deleted_count
        }
    
    except Exception as e:
        logger.error(f"Bulk delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
