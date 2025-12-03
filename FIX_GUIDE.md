# Fix Guide for Reconciliation Errors

## Issues Fixed

### 1. Database Schema Error
**Error**: `la colonne « execution_time_ms » de la relation « audit_logs » n'existe pas`

**Solution**: Run the migration script to add the missing column.

### 2. Gemini API Quota Exceeded
**Error**: `429 You exceeded your current quota`

**Solutions**:
- Added rate limiting (8 requests/minute instead of 10 for safety)
- Reduced AI calls by only categorizing suspense items when count ≤ 20
- Added automatic fallback to fuzzy matching when AI fails

## Steps to Fix

### Step 1: Run Database Migration

```bash
cd backend
python run_migration.py
```

This will add the missing `execution_time_ms` column to the `audit_logs` table.

### Step 2: Restart Backend Server

```bash
# Stop the current server (Ctrl+C)
python start.py
```

The rate limiting is now automatically applied to all AI calls.

### Step 3: Test Reconciliation

Upload your files and run reconciliation. The system will now:
- Respect API rate limits (max 8 requests/minute)
- Skip AI categorization for large suspense lists (>20 items)
- Automatically fallback to fuzzy matching if AI fails

## Configuration Options

### Disable AI Assistance Completely

If you want to avoid API quota issues entirely, disable AI in your reconciliation request:

```json
{
  "bank_file": "file-id",
  "accounting_file": "file-id",
  "rules": {
    "enable_ai_assistance": false
  }
}
```

### Adjust Rate Limiting

Edit `backend/services/ai_assistant.py`:

```python
MAX_REQUESTS_PER_MINUTE = 5  # More conservative (default: 8)
```

## Monitoring

Check AI performance metrics:
```bash
GET /api/ai/metrics
```

Response includes:
- `total_calls`: Total AI requests
- `failed_calls`: Failed requests
- `fallback_used`: Times fallback was used
- `success_rate`: Percentage of successful calls

## Alternative: Use Gemini API with Higher Quota

1. Upgrade to Gemini API paid tier
2. Or migrate to `gemini-2.0-flash-preview-image-generation` as suggested in error
3. Update `backend/config.py`:

```python
AI_CONFIG = {
    "model_name": "gemini-2.0-flash-preview-image-generation",
    "temperature": 0.1,
    "timeout": 5
}
```

## Troubleshooting

### If migration fails:

```bash
# Connect to PostgreSQL
psql -U your_user -d your_database

# Manually add column
ALTER TABLE audit_logs ADD COLUMN execution_time_ms INTEGER;
```

### If rate limiting is too slow:

Disable AI assistance in reconciliation rules (see Configuration Options above).

### If you still get quota errors:

Wait 60 seconds between reconciliation runs to reset the rate limit window.
