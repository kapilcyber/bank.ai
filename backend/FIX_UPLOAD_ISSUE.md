# 🔧 Fix: Resume Upload Not Increasing Count

## Problem Identified

When uploading resumes through the admin portal, the count was not increasing because of a **unique constraint violation**.

### Root Cause

The `resumes` table has a unique constraint on `(source_type, source_id)`:
```sql
CONSTRAINT uq_resume_source UNIQUE (source_type, source_id)
```

For admin uploads, `source_id` was set to `None`. While PostgreSQL allows multiple NULLs in unique constraints, the constraint was preventing proper inserts in some cases.

## Solution Applied

### 1. Generate Unique `source_id` for Admin Uploads

Changed admin upload endpoints to generate a unique `source_id` for each upload:
```python
import uuid
from datetime import datetime

admin_source_id = f"admin_{uuid.uuid4().hex[:16]}_{int(datetime.utcnow().timestamp() * 1000)}"
```

This ensures:
- Each admin upload gets a unique identifier
- No unique constraint violations
- All uploads are saved successfully

### 2. Files Modified

1. **`techbankai/backend/src/routes/resume.py`**
   - Added `import uuid`
   - Generate unique `source_id` for admin uploads
   - Added logging to track uploads

2. **`techbankai/backend/src/routes/resumes/admin.py`**
   - Added `import uuid` and `from datetime import datetime`
   - Generate unique `source_id` for bulk admin uploads

### 3. Backend Logging Enhanced

Added detailed logging:
- `"Creating new resume record for admin upload: [filename] (source_id: [id])"`
- `"Resume saved to database with ID: [id]"`
- `"Total resumes in database after upload: [count]"`

## Testing

### Steps to Verify Fix

1. **Restart backend server** (required for code changes)
2. **Upload a new resume** via admin portal
3. **Check backend logs** - Should see:
   - Resume created with unique source_id
   - Total count increased
4. **Check admin dashboard** - Count should increase
5. **Check Records tab** - New resume should appear

### Expected Behavior

- ✅ Each upload creates a new record
- ✅ Count increases with each upload
- ✅ No unique constraint errors
- ✅ All resumes appear in Records

## Database Verification

To verify resumes are being saved:
```powershell
cd techbankai\backend
python scripts\verify_resumes.py
```

Or directly in PostgreSQL:
```sql
SELECT COUNT(*) FROM resumes;
SELECT id, filename, source_type, source_id, uploaded_at 
FROM resumes 
ORDER BY uploaded_at DESC 
LIMIT 10;
```

## Notes

- User uploads (guest, freelancer, company employee) still use `source_id=None` because they have duplicate checking by email
- Admin uploads now always create new records with unique source_ids
- The unique constraint still works for other source types (company_employee with employee_id, etc.)
