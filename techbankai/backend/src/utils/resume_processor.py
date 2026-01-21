from sqlalchemy import delete
from src.models.resume import Resume, Experience, Certification, Education

async def save_structured_resume_data(db, resume_id, parsed_data, clear_existing=False, form_education=None, form_experiences=None):
    """
    Extracts and saves structured Experience and Certification records 
    from parsed_data JSON into dedicated tables.
    """
    try:
        if clear_existing:
            await db.execute(delete(Experience).where(Experience.resume_id == resume_id))
            await db.execute(delete(Certification).where(Certification.resume_id == resume_id))
            await db.execute(delete(Education).where(Education.resume_id == resume_id))

        # 1. Save Certifications
        certs = parsed_data.get("resume_certificates", [])
        for cert_name in certs:
            if cert_name and cert_name != "Not mentioned":
                new_cert = Certification(
                    resume_id=resume_id,
                    name=cert_name,
                    issuer="Detected"
                )
                db.add(new_cert)

        # 2. Save Experience (prioritize form_experiences, then parsed_data)
        experience_list = None
        experience_saved_count = 0
        
        # First, try to use form_experiences if provided (from frontend)
        if form_experiences:
            import json
            try:
                if isinstance(form_experiences, str):
                    # Try to parse as JSON first
                    if form_experiences.strip().startswith('[') or form_experiences.strip().startswith('{'):
                        experience_list = json.loads(form_experiences)
                    else:
                        # If not JSON, skip (legacy single string not supported for experiences)
                        experience_list = None
                elif isinstance(form_experiences, list):
                    experience_list = form_experiences
            except (json.JSONDecodeError, TypeError) as e:
                # If parsing fails, skip
                experience_list = None
        
        # Fallback to parsed_data if form_experiences not available
        if not experience_list:
            # Try to get from parsed_data (could be a list or single entry)
            experience_list = parsed_data.get("resume_experience_list") or parsed_data.get("work_experience") or []
            # If still empty, create from primary role (legacy support)
            if not experience_list:
                role = parsed_data.get("resume_role") or parsed_data.get("role")
                if role and role != "Not mentioned":
                    experience_list = [{
                        "role": role,
                        "company": parsed_data.get("resume_company") or "Detected",
                        "description": parsed_data.get("resume_summary") or ""
                    }]
        
        # Process experience list
        if experience_list:
            if isinstance(experience_list, list):
                for exp in experience_list:
                    # Skip empty entries
                    if not exp or exp == "Not mentioned":
                        continue
                    
                    if isinstance(exp, dict):
                        # Only save if at least role or company is provided
                        role = exp.get("role") or ""
                        company = exp.get("company") or ""
                        
                        if role or company:
                            new_exp = Experience(
                                resume_id=resume_id,
                                role=role or "Not specified",
                                company=company or "Detected",
                                location=exp.get("location") or exp.get("city"),
                                start_date=exp.get("start_date") or exp.get("start_year") or exp.get("startDate"),
                                end_date=exp.get("end_date") or exp.get("end_year") or exp.get("endDate"),
                                is_current=1 if exp.get("is_current") or exp.get("isCurrent") or (exp.get("end_date") == "Present" or exp.get("endDate") == "Present") else 0,
                                description=exp.get("description") or exp.get("summary") or exp.get("details")
                            )
                            db.add(new_exp)
                            experience_saved_count += 1
                    else:
                        # Non-dict entry, skip (experiences should be structured)
                        pass
            elif isinstance(experience_list, dict):
                # Single experience object
                role = experience_list.get("role") or ""
                company = experience_list.get("company") or ""
                if role or company:
                    new_exp = Experience(
                        resume_id=resume_id,
                        role=role or "Not specified",
                        company=company or "Detected",
                        location=experience_list.get("location"),
                        start_date=experience_list.get("start_date") or experience_list.get("start_year"),
                        end_date=experience_list.get("end_date") or experience_list.get("end_year"),
                        is_current=1 if experience_list.get("is_current") or experience_list.get("end_date") == "Present" else 0,
                        description=experience_list.get("description")
                    )
                    db.add(new_exp)
                    experience_saved_count += 1
        
        # 3. Save Education (prioritize form_education, then parsed_data)
        education_list = None
        education_saved_count = 0
        
        # First, try to use form_education if provided (from frontend)
        if form_education:
            import json
            try:
                if isinstance(form_education, str):
                    # Try to parse as JSON first
                    if form_education.strip().startswith('[') or form_education.strip().startswith('{'):
                        education_list = json.loads(form_education)
                    else:
                        # If not JSON, treat as single string entry
                        if form_education.strip():
                            education_list = [{"degree": form_education.strip()}]
                elif isinstance(form_education, list):
                    education_list = form_education
            except (json.JSONDecodeError, TypeError) as e:
                # If parsing fails, treat as single string entry
                if form_education and str(form_education).strip():
                    education_list = [{"degree": str(form_education).strip()}]
        
        # Fallback to parsed_data if form_education not available
        if not education_list:
            # Try multiple keys from parsed_data
            education_list = parsed_data.get("resume_education_list") or parsed_data.get("resume_education") or []
        
        # Process education list
        if education_list:
            if isinstance(education_list, str):
                # If it's a string, try to parse it or create a single entry
                if education_list and education_list != "Not mentioned":
                    new_edu = Education(
                        resume_id=resume_id,
                        degree=education_list,
                        institution="Detected"
                    )
                    db.add(new_edu)
                    education_saved_count += 1
            elif isinstance(education_list, list):
                for edu in education_list:
                    # Skip empty entries
                    if not edu or edu == "Not mentioned":
                        continue
                    
                    if isinstance(edu, dict):
                        # Only save if at least degree or institution is provided
                        degree = edu.get("degree") or edu.get("name") or ""
                        institution = edu.get("institution") or edu.get("school") or edu.get("college") or ""
                        
                        if degree or institution:
                            new_edu = Education(
                                resume_id=resume_id,
                                degree=degree or "Not specified",
                                institution=institution or "Detected",
                                field_of_study=edu.get("field_of_study") or edu.get("field") or edu.get("stream"),
                                start_date=edu.get("start_date") or edu.get("start_year"),
                                end_date=edu.get("end_date") or edu.get("end_year"),
                                grade=edu.get("grade") or edu.get("cgpa") or edu.get("percentage"),
                                description=edu.get("description") or edu.get("details")
                            )
                            db.add(new_edu)
                            education_saved_count += 1
                    else:
                        # Non-dict entry, convert to string
                        edu_str = str(edu).strip()
                        if edu_str and edu_str != "Not mentioned":
                            new_edu = Education(
                                resume_id=resume_id,
                                degree=edu_str,
                                institution="Detected"
                            )
                            db.add(new_edu)
                            education_saved_count += 1
            
        return True
    except Exception as e:
        import traceback
        error_msg = f"Error saving structured data for resume_id {resume_id}: {e}\n{traceback.format_exc()}"
        print(error_msg)
        # Log to logger if available
        try:
            from src.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(error_msg)
        except:
            pass
        return False
