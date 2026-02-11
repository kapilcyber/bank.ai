# 🔍 Troubleshooting: Resume Upload Not Increasing Count

## Quick Checks

### 1. **Restart Backend Server** ⚠️ CRITICAL
The code changes require a server restart:
```powershell
# Stop the server (Ctrl+C)
# Then restart:
cd techbankai
.\start-backend.ps1
```

### 2. **Check Backend Logs**
After uploading, check the backend console for:
- `"Creating new resume record for admin upload: [filename]"`
- `"Resume saved to database with ID: [id]"`
- `"Total resumes in database after upload: [count]"`

If you see these messages, the resume IS being saved.

### 3. **Check Browser Console**
Open browser DevTools (F12) → Console tab:
- Look for: `"📤 Upload response:"`
- Look for: `"🔄 Dispatching resumeUploaded event"`
- Look for: `"📥 AdminDashboard: Received resumeUploaded event"`
- Look for: `"🔄 AdminDashboard: Refreshing dashboard data..."`

### 4. **Verify Database Count**
Run this script to check actual database count:
```powershell
cd techbankai\backend
python scripts\test_upload.py
```

### 5. **Check Upload Response**
After upload, the frontend should show:
- Success message: `"Successfully uploaded X resumes"`
- Check if `response.success > 0`

## Common Issues

### Issue 1: Server Not Restarted
**Symptom**: Count stays at 40 even after upload
**Fix**: Restart backend server

### Issue 2: Upload Failing Silently
**Symptom**: No error message but count doesn't increase
**Check**: 
- Browser console for errors
- Backend logs for exceptions
- Network tab in DevTools (check API response)

### Issue 3: Frontend Not Refreshing
**Symptom**: Resume saved but UI doesn't update
**Fix**: 
- Manually refresh the page
- Check browser console for event dispatch logs
- Verify `resumeUploaded` event is being fired

### Issue 4: Database Transaction Not Committed
**Symptom**: Resume appears in logs but not in database
**Check**: Backend logs for commit errors

## Manual Verification

1. **Upload a resume**
2. **Check backend logs** - Should see:
   ```
   Creating new resume record for admin upload: [filename]
   Resume saved to database with ID: [id]
   Total resumes in database after upload: [count]
   ```
3. **Check browser console** - Should see event dispatch logs
4. **Run test script**:
   ```powershell
   python scripts\test_upload.py
   ```
5. **Check database directly**:
   ```sql
   SELECT COUNT(*) FROM resumes;
   SELECT id, filename, uploaded_at FROM resumes ORDER BY uploaded_at DESC LIMIT 5;
   ```

## If Still Not Working

1. **Clear browser cache** and refresh
2. **Check network tab** - Verify API call returns 200 OK
3. **Check response data** - Verify `success` field > 0
4. **Check backend error logs** - Look for exceptions
5. **Verify database connection** - Run `python scripts\verify_resumes.py`
