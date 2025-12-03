# Rapprochement Bancaire - Backend Implementation Guide

## 🎯 Architecture Overview

This backend implements a **production-ready** bank reconciliation system following Tunisian accounting standards (PCN) with controlled AI assistance.

### Core Components

```
backend/
├── routes/              # API endpoints
│   ├── auth_routes.py          # Authentication & authorization
│   ├── upload_routes.py        # File upload & processing
│   ├── reconcile_routes.py     # Reconciliation engine
│   └── ai_routes.py            # AI assistant endpoints
├── services/            # Business logic
│   ├── matching_engine.py      # 5-tier matching algorithm
│   ├── file_processor.py       # CSV parsing & normalization
│   ├── ai_assistant.py         # Gemini AI integration
│   ├── pcn_service.py          # Tunisian PCN validation
│   ├── regularization_service.py # Accounting entries generation
│   ├── database_service.py     # Database operations
│   └── export_service.py       # Excel/PDF export
├── db_models/           # SQLAlchemy models
│   ├── users.py
│   ├── files.py
│   ├── transactions.py
│   ├── reconciliation.py
│   └── audit.py
└── utils/               # Utilities
    ├── logger.py
    └── helpers.py
```

## 🔧 Reconciliation Engine - 5 Tiers

### Tier 1: Exact Match (95%+ similarity)
- Amount tolerance: ±0.01 TND
- Date tolerance: ±1 day
- Label similarity: ≥95%

### Tier 2: Strong Fuzzy Match (80%+ similarity)
- Amount tolerance: ±0.01 TND
- Date tolerance: ±3 days
- Label similarity: ≥80%

### Tier 3: AI-Assisted Match (70%+ AI confidence)
- Uses Gemini 2.0 Flash for label comparison
- Amount tolerance: ±0.02 TND
- Date tolerance: ±7 days
- AI similarity threshold: ≥70%

### Tier 4: Weak Fuzzy Match (60%+ similarity)
- Amount tolerance: ±1 TND
- Date tolerance: ±7 days
- Label similarity: ≥60%

### Tier 5: Group Matching (1-to-N)
- Matches one bank transaction to multiple accounting entries
- Maximum group size: 5 entries
- Sum must match within tolerance

## 🤖 AI Integration - Controlled Approach

### Gemini API Configuration
```python
AI_CONFIG = {
    "temperature": 0.1,        # Very low to reduce hallucination
    "max_output_tokens": 50,   # Limited output
    "model_name": "gemini-2.0-flash-exp"
}
```

### AI Use Cases (STRICTLY LIMITED)

#### 1. Label Similarity Comparison
```python
compare_labels(label1: str, label2: str) -> float
```
- Returns similarity score 0.0 to 1.0
- Used in Tier 3 matching only
- Fallback to fuzzy matching if AI fails

#### 2. Transaction Categorization
```python
categorize_transaction(description: str) -> dict
```
- Categories: FRAIS_BANCAIRE, VIREMENT_RECU, VIREMENT_EMIS, CHEQUE, etc.
- Returns category + confidence score
- User validation required

#### 3. PCN Account Validation
```python
validate_pcn_account(account_code: str) -> dict
```
- Validates against Tunisian PCN structure
- Returns valid/invalid + confidence
- Suggests alternatives if invalid

#### 4. Account Mapping Suggestion
```python
suggest_account_mapping(description: str, amount: float) -> dict
```
- Suggests PCN account based on transaction
- Returns account code + confidence
- Never auto-applies, only suggests

### AI Safety Measures
- ✅ Timeout: 5 seconds maximum
- ✅ Error handling: Falls back to manual methods
- ✅ No financial decisions: AI only suggests, never decides
- ✅ Audit trail: All AI calls logged
- ✅ Validation required: User must confirm all AI suggestions

## 📊 PCN Service - Tunisian Chart of Accounts

### Complete PCN Implementation

The `pcn_service.py` contains the full Tunisian PCN with 100+ accounts:

**Class 1**: Capital accounts (10xxxx)
**Class 2**: Fixed assets (2xxxxx)
**Class 3**: Inventory (3xxxxx)
**Class 4**: Third parties (4xxxxx) - Most used in reconciliation
**Class 5**: Financial accounts (5xxxxx) - Critical for bank reconciliation
**Class 6**: Expenses (6xxxxx)
**Class 7**: Revenue (7xxxxx)

### Key Accounts for Reconciliation

```python
"512000": "Banques"                              # Main bank account
"627100": "Commissions bancaires"                # Bank fees
"627200": "Intérêts bancaires"                   # Debit interest
"768000": "Intérêts et produits assimilés"       # Credit interest
"471000": "Comptes transitoires ou d'attente"    # Suspense account
"511200": "Caisse - Chèques à encaisser"         # Checks to deposit
"401000": "Fournisseurs"                         # Suppliers
"411000": "Clients"                              # Customers
```

## 📝 Regularization Service

### Automatic Entry Generation

The system automatically generates accounting entries for suspense items:

#### Bank Suspense (Bank → Accounting)
```
Example: Bank fee not recorded
Debit:  627100 (Bank fees)      50.00 TND
Credit: 512000 (Bank)            50.00 TND
```

#### Accounting Suspense (Accounting → Bank)
```
Example: Check issued but not cashed
Debit:  511200 (Checks)         1000.00 TND
Credit: 512000 (Bank)           1000.00 TND
```

### Entry Validation

All generated entries are validated:
- ✅ Debit = Credit (balanced)
- ✅ Valid PCN accounts
- ✅ Proper account types
- ✅ Correct signs (debit/credit)

## 🗄️ Database Architecture

### Key Tables

**users**: User accounts with roles (admin/user)
**uploaded_files**: File metadata and processing status
**bank_transactions**: Parsed bank transactions
**accounting_transactions**: Parsed accounting entries
**reconciliations**: Reconciliation jobs with results
**matches**: Individual transaction matches
**suspense_items**: Unmatched transactions
**audit_logs**: Complete audit trail

### Data Flow

1. User uploads CSV files → `uploaded_files`
2. Files parsed → `bank_transactions` + `accounting_transactions`
3. Reconciliation runs → `reconciliations` + `matches` + `suspense_items`
4. User validates → `audit_logs`
5. Export generated → Reports

## 📤 Export Service

### Excel Export (Multi-sheet)
- **Sheet 1**: Summary with key metrics
- **Sheet 2**: All matches with N° R
- **Sheet 3**: Suspense items with AI suggestions
- **Sheet 4**: Regularization entries (PCN format)

### PDF Export
- Professional report format
- Summary tables
- Match details (first 50)
- Suitable for printing/archiving

### CSV Export (ERP Import)
- Standard accounting format
- Compatible with Sage, TSI, etc.
- Journal code: OD (Operations Diverses)
- Ready for direct import

## 🔒 Security & Compliance

### Authentication
- JWT tokens with 30-minute expiration
- Password hashing with bcrypt
- Role-based access control (RBAC)

### Data Protection
- File encryption at rest
- Secure file upload validation
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection (FastAPI)

### Audit Trail
- All actions logged with user ID
- Timestamp and IP address
- Entity type and entity ID
- Action details in JSON

### Tunisian Compliance
- ✅ PCN conformity
- ✅ N° R (reconciliation numbers) generation
- ✅ Lettrage/Pointage support
- ✅ Audit trail for tax authorities
- ✅ Data retention policies

## 🚀 Performance Optimizations

### Matching Engine
- Pandas vectorized operations
- Early termination on exact matches
- Indexed lookups for candidates
- Batch processing for large datasets

### Database
- Indexed foreign keys
- Pagination for large result sets
- Connection pooling
- Query optimization

### Caching
- In-memory cache for reconciliation results
- Redis recommended for production
- Cache invalidation on updates

## 📈 Monitoring & Metrics

### Performance Metrics
- Processing time per reconciliation
- Match rate by tier
- AI call success rate
- Export generation time

### Quality Metrics
- Match accuracy (validated vs rejected)
- AI suggestion acceptance rate
- Suspense resolution rate
- User satisfaction

### System Metrics
- API response times
- Database query performance
- File upload success rate
- Error rates by endpoint

## 🧪 Testing Strategy

### Unit Tests
- Matching engine algorithms
- PCN validation logic
- Regularization entry generation
- AI assistant functions

### Integration Tests
- End-to-end reconciliation flow
- File upload and processing
- Database operations
- Export generation

### Load Tests
- 10,000+ transactions
- Concurrent users
- Large file uploads
- Export performance

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=sqlite:///./reconciliation.db  # Use PostgreSQL in production

# AI
GEMINI_API_KEY=your_gemini_api_key

# Security
SECRET_KEY=your_secret_key_change_in_production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Storage
UPLOAD_DIR=storage/uploads
REPORT_DIR=storage/reports
LOG_DIR=storage/logs
```

### Reconciliation Rules (Configurable)
```python
ReconciliationRules(
    amount_tolerance=0.01,
    date_tolerance_days=1,
    fuzzy_date_tolerance_days=3,
    weak_date_tolerance_days=7,
    label_similarity_threshold=0.95,
    fuzzy_label_threshold=0.80,
    weak_label_threshold=0.60,
    enable_group_matching=True,
    max_group_size=5,
    enable_ai_assistance=True
)
```

## 🚀 Deployment

### Production Checklist
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set strong SECRET_KEY
- [ ] Configure Redis for caching
- [ ] Enable HTTPS
- [ ] Set up backup strategy
- [ ] Configure logging (ELK stack)
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure rate limiting
- [ ] Set up CI/CD pipeline
- [ ] Document API with Swagger

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📚 API Documentation

API documentation available at: `http://localhost:8000/docs`

### Key Endpoints

**Authentication**
- POST `/api/auth/login` - User login
- POST `/api/auth/register` - User registration
- GET `/api/auth/me` - Get current user

**Upload**
- POST `/api/upload/bank` - Upload bank CSV
- POST `/api/upload/accounting` - Upload accounting CSV

**Reconciliation**
- POST `/api/reconcile` - Start reconciliation
- GET `/api/reconcile/{job_id}/results` - Get results
- POST `/api/reconcile/{job_id}/matches/{match_id}/validate` - Validate match
- GET `/api/reconcile/{job_id}/export` - Export results
- GET `/api/reconcile/{job_id}/regularization` - Get regularization entries

**AI Assistant**
- POST `/api/ai/similarity` - Compare label similarity
- POST `/api/ai/categorize` - Categorize transaction
- POST `/api/ai/validate-pcn` - Validate PCN account
- POST `/api/ai/suggest-account` - Suggest account mapping

## 🎓 Best Practices

### Code Quality
- Type hints for all functions
- Docstrings for all classes/methods
- PEP 8 compliance
- Error handling with proper exceptions
- Logging at appropriate levels

### Database
- Use transactions for multi-step operations
- Index frequently queried columns
- Avoid N+1 queries
- Use connection pooling
- Regular backups

### Security
- Never log sensitive data
- Validate all inputs
- Use parameterized queries
- Implement rate limiting
- Regular security audits

## 📞 Support

For issues or questions:
- Check logs in `storage/logs/reconciliation.log`
- Review API documentation at `/docs`
- Check database integrity
- Verify Gemini API key is valid
- Ensure all dependencies are installed

## 🔄 Future Enhancements

- [ ] Multi-currency support
- [ ] OCR for PDF bank statements
- [ ] Machine learning for pattern recognition
- [ ] Real-time reconciliation
- [ ] Mobile app integration
- [ ] Blockchain audit trail
- [ ] Advanced analytics dashboard
- [ ] Integration with major Tunisian banks APIs
