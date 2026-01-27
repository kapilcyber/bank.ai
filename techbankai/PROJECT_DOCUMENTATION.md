# TechBank.Ai - Project Documentation

## Project Overview

**TechBank.Ai** is an AI-powered resume screening and job description analysis platform that helps organizations efficiently match candidates with job requirements. The system uses advanced AI (GPT-4) for intelligent resume parsing, job description analysis, and semantic candidate matching.

---

## Description  

TechBank.Ai is a comprehensive talent management platform that automates the resume screening process. It enables HR teams and recruiters to:

- Upload and parse resumes using AI-powered extraction
- Analyze job descriptions to extract key requirements
- Automatically match candidates to job postings with intelligent scoring
- Manage multiple user types (Company Employees, Freelancers, Guest Users, Hired Forces)
- Access detailed analytics and insights through an admin dashboard
- Search and filter talent based on skills, experience, location, and more

The platform solves the time-consuming manual process of screening hundreds of resumes by leveraging AI to understand context, skills, and experience beyond simple keyword matching.

---

## Use Cases

### Primary Use Cases

1. **Resume Screening Automation**
   - HR teams upload job descriptions and receive automatically ranked candidate matches
   - Reduces screening time from hours to minutes
   - Identifies best-fit candidates based on skills, experience, and semantic understanding

2. **Talent Pool Management**
   - Centralized database of all candidates (employees, freelancers, applicants)
   - Search and filter candidates by skills, location, experience level
   - Track candidate profiles and qualifications

3. **Recruitment Analytics**
   - Dashboard with statistics on user types, skills distribution, geographic distribution
   - Trend analysis (daily, monthly, quarterly)
   - Role-based candidate insights

4. **Multi-Source Resume Collection**
   - Company employee uploads
   - Freelancer registrations
   - Guest user applications
   - Gmail/Outlook email integration for automated resume collection

5. **Job Description Analysis**
   - Extract required/preferred skills from job descriptions
   - Identify experience requirements
   - Generate keyword lists for matching

---

## Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Programming language |
| FastAPI | 0.104.1 | Web framework |
| PostgreSQL | 15+ | Primary database |
| SQLAlchemy | 2.0.23 | ORM |
| OpenAI GPT-4 | Latest | AI-powered parsing and matching |
| JWT (python-jose) | 3.3.0 | Authentication |
| Uvicorn | 0.24.0 | ASGI server |
| Celery | 5.3.4 | Background task processing |
| Redis | 4.5.2+ | Task queue and caching |
| Pydantic | 2.5.0+ | Data validation |
| pdfplumber | 0.10.3 | PDF text extraction |
| python-docx | 1.1.0 | DOCX file processing |
| Google API Client | 2.108.0 | Google Drive integration |
| MSAL | 1.24.0+ | Microsoft Outlook integration |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.2.0 | UI library |
| React Router | 6.20.0 | Client-side routing |
| Vite | 5.0.8 | Build tool and dev server |
| Framer Motion | 10.16.16 | Animations |
| Recharts | 3.6.0 | Data visualization |
| JWT Decode | 4.0.0 | Token decoding |
| React OAuth Google | 0.13.4 | Google authentication |

### Infrastructure & Tools
| Technology | Purpose |
|------------|---------|
| PostgreSQL | Database |
| Redis | Task queue and caching |
| Nginx | Reverse proxy (optional) |
| Alembic | Database migrations |
| Ruff | Python linter |
| Pytest | Testing framework |

---

## Features Table

| Feature ID | Feature Name | Description | Tech Stack | Use Case | Owner |
|------------|---------------|-------------|------------|----------|-------|
| F001 | User Authentication | JWT-based authentication with signup, login, logout, and password reset functionality | FastAPI, JWT, bcrypt, PostgreSQL | Secure user access and session management | TBD |
| F002 | User Registration | Multi-type user registration (Company Employee, Freelancer, Guest User, Hired Forces) with ID verification | FastAPI, PostgreSQL, CSV validation | Onboard different user types with role-based access | TBD |
| F003 | Resume Upload (User Profile) | Users can upload their own resume/profile (PDF/DOCX) | FastAPI, pdfplumber, python-docx, PostgreSQL | Allow users to create and update their profiles | TBD |
| F004 | Resume Upload (Company Employee) | Company employees upload resumes with employee ID verification | FastAPI, file processing, CSV validation | Manage internal employee talent pool | TBD |
| F005 | Resume Upload (Admin Bulk) | Admin can bulk upload multiple resumes at once | FastAPI, file processing, async operations | Efficiently add multiple candidates to the system | TBD |
| F006 | AI-Powered Resume Parsing | Extract structured data from resumes using GPT-4 (name, email, skills, experience, education, etc.) | OpenAI GPT-4, FastAPI, Pydantic | Automatically parse unstructured resume data | TBD |
| F007 | Job Description Upload | Upload JD files (PDF/DOCX) or enter text manually | FastAPI, pdfplumber, python-docx | Input job requirements for matching | TBD |
| F008 | AI-Powered JD Analysis | Extract requirements from job descriptions using GPT-4 (skills, experience, education, keywords) | OpenAI GPT-4, FastAPI | Understand job requirements intelligently | TBD |
| F009 | Traditional Candidate Matching | Fast keyword-based matching (skills, experience, keywords) | Python, SQLAlchemy, PostgreSQL | Quick initial candidate filtering | TBD |
| F010 | AI Semantic Matching | GPT-4 powered semantic understanding for context-aware matching | OpenAI GPT-4, FastAPI | Match candidates beyond keywords | TBD |
| F011 | Hybrid Scoring System | Combined scoring (0-100) using traditional + AI matching (40% skills, 30% experience, 30% semantic) | Python, OpenAI GPT-4 | Accurate candidate ranking | TBD |
| F012 | Match Results Storage | Store JD analysis and match results in database with detailed scoring breakdown | PostgreSQL, SQLAlchemy | Track and retrieve matching history | TBD |
| F013 | Talent Search | Search candidates by skills, location, experience, role, user type | FastAPI, PostgreSQL, SQLAlchemy | Find specific candidates in the database | TBD |
| F014 | Admin Dashboard | Comprehensive statistics dashboard with charts and analytics | React, Recharts, FastAPI | Monitor system usage and insights | TBD |
| F015 | User Statistics | View total users, resumes, JD analyses, matches | PostgreSQL, FastAPI | Track system metrics | TBD |
| F016 | User Type Breakdown | Statistics by user type (Company Employee, Freelancer, Guest User) | PostgreSQL, FastAPI, React | Understand user distribution | TBD |
| F017 | Skills Distribution | Most common skills across all candidates | PostgreSQL, FastAPI, React | Identify popular skills in talent pool | TBD |
| F018 | Geographic Distribution | Candidate distribution by Indian states | PostgreSQL, FastAPI, React, Choropleth maps | Understand geographic talent spread | TBD |
| F019 | Experience Distribution | Candidate distribution by years of experience | PostgreSQL, FastAPI, React | Analyze experience levels in talent pool | TBD |
| F020 | Role-Based Insights | Candidates grouped by job roles with experience levels | PostgreSQL, FastAPI, React | Find candidates for specific roles | TBD |
| F021 | Upload Trends | Daily, monthly, quarterly upload trends | PostgreSQL, FastAPI, React, Recharts | Track growth and activity patterns | TBD |
| F022 | User Management | Admin can view, delete users | FastAPI, PostgreSQL | Manage user accounts | TBD |
| F023 | Resume Management | View, search, delete resumes | FastAPI, PostgreSQL | Manage candidate resumes | TBD |
| F024 | JD Analysis History | View past job description analyses and results | PostgreSQL, FastAPI, React | Access previous matching results | TBD |
| F025 | Match Result Details | View detailed match scores (skill, experience, semantic) and explanations | PostgreSQL, FastAPI, React | Understand why candidates matched | TBD |
| F026 | File Storage | Secure file storage for resumes and JD files | FastAPI, aiofiles, local storage | Store uploaded documents | TBD |
| F027 | Google Drive Integration | Import resumes from Google Drive | Google API Client, FastAPI | Automated resume collection | TBD |
| F028 | Gmail Integration | Webhook-based resume extraction from Gmail | Google API Client, FastAPI | Automated resume collection from emails | TBD |
| F029 | Outlook Integration | Resume extraction from Microsoft Outlook | MSAL, FastAPI | Automated resume collection from Outlook | TBD |
| F030 | Protected Routes | Frontend route protection based on authentication and admin status | React Router, JWT | Secure frontend navigation | TBD |
| F031 | Profile Page | User profile viewing and editing | React, FastAPI | Users can view and update their profiles | TBD |
| F032 | Landing Page | Public landing page with information | React | Marketing and information page | TBD |
| F033 | Error Handling | Comprehensive error handling with trace IDs | FastAPI, Python | Debug and monitor errors | TBD |
| F034 | Request Logging | Log all API requests and responses | FastAPI, Python logging | Monitor API usage | TBD |
| F035 | Token Blacklist | JWT token revocation for logout | PostgreSQL, FastAPI | Secure session management | TBD |
| F036 | Password Reset | Email-based password reset with verification codes | FastAPI, Python | Recover forgotten passwords | TBD |
| F037 | Employment Type Selection | UI for selecting employment type (Company Employee, Freelancer, Guest User, Hired Forces) | React, Framer Motion | User onboarding flow | TBD |
| F038 | Drag & Drop File Upload | User-friendly file upload interface | React, HTML5 | Easy resume upload experience | TBD |
| F039 | File Validation | Validate file type (PDF, DOCX) and size (max 10MB) | FastAPI, Python | Ensure file quality and security | TBD |
| F040 | Responsive Design | Mobile-friendly responsive UI | React, CSS3 | Access from any device | TBD |
| F041 | Animations | Smooth UI animations using Framer Motion | React, Framer Motion | Enhanced user experience | TBD |
| F042 | Data Visualization | Charts and graphs for analytics (Recharts) | React, Recharts | Visual data representation | TBD |
| F043 | Database Migrations | Alembic-based database schema migrations | Alembic, PostgreSQL | Version-controlled database changes | TBD |
| F044 | Background Tasks | Celery-based asynchronous task processing | Celery, Redis | Handle long-running operations | TBD |
| F045 | CORS Configuration | Cross-origin resource sharing setup | FastAPI, CORS middleware | Frontend-backend communication | TBD |
| F046 | Health Check Endpoint | System health monitoring endpoint | FastAPI | Monitor system availability | TBD |
| F047 | API Documentation | Auto-generated Swagger/OpenAPI documentation | FastAPI | Developer-friendly API docs | TBD |
| F048 | CSV Validation | Validate employee IDs and freelancer IDs from CSV files | Python, CSV parsing | Ensure data integrity | TBD |
| F049 | State Normalization | Normalize Indian states and cities for geographic analysis | Python, PostgreSQL | Consistent geographic data | TBD |
| F050 | Role Normalization | Normalize job roles for consistent categorization | Python, PostgreSQL | Consistent role classification | TBD |

---

## Database Schema

### Core Tables

1. **users** - User accounts with authentication
2. **resumes** - Resume data and parsed information
3. **jd_analysis** - Job description analyses
4. **match_results** - Candidate matching results with scores
5. **token_blacklist** - Revoked JWT tokens
6. **work_history** - Employment history for resumes
7. **educations** - Education records for resumes
8. **certificates** - Certification records for resumes

---

## API Endpoints Summary

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/verify-code` - Verify reset code
- `POST /api/auth/reset-password` - Reset password

### Resume Management
- `POST /api/resumes/upload/user-profile` - Upload user resume
- `POST /api/resumes/upload/company` - Upload company employee resume
- `POST /api/resumes/upload/admin` - Admin bulk upload
- `GET /api/resumes` - List all resumes
- `GET /api/resumes/{id}` - Get resume details
- `DELETE /api/resumes/{id}` - Delete resume
- `GET /api/resumes/search` - Search resumes

### JD Analysis
- `POST /api/jd/analyze` - Analyze JD and get matches
- `GET /api/jd/results/{job_id}` - Get analysis results
- `GET /api/jd/history` - Get analysis history

### Admin
- `GET /api/admin/stats` - Dashboard statistics
- `GET /api/admin/users` - List users
- `DELETE /api/admin/users/{id}` - Delete user

### System
- `GET /health` - Health check
- `GET /docs` - API documentation (Swagger)
- `GET /redoc` - API documentation (ReDoc)

---

## Project Structure

```
techbankai/
├── backend/
│   ├── src/
│   │   ├── main.py              # FastAPI application entry
│   │   ├── config/             # Configuration (database, settings)
│   │   ├── models/             # Database models
│   │   ├── routes/             # API routes
│   │   ├── services/           # Business logic (parsing, matching, AI)
│   │   ├── middleware/         # Auth, error handling
│   │   ├── utils/              # Utilities (logging, validation)
│   │   └── workers/            # Celery background tasks
│   ├── tests/                  # Test suite
│   ├── uploads/                # File storage
│   ├── alembic/                # Database migrations
│   └── requirements.txt        # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx            # React entry point
│   │   ├── App.jsx             # Main app component
│   │   ├── pages/              # Page components
│   │   ├── components/         # Reusable components
│   │   ├── config/             # API configuration
│   │   └── context/            # React context
│   ├── package.json            # Node dependencies
│   └── vite.config.js          # Vite configuration
│
└── README.md                   # Main project README
```

---

## Environment Variables

### Backend (.env)
```env
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=techbank
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Server
HOST=0.0.0.0
PORT=5000

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# CORS
CORS_ORIGINS=http://localhost:5173

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0
```

---

## Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis (for background tasks)
- OpenAI API Key

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m src.main
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## Key Algorithms & Processes

### Resume Parsing Flow
1. User uploads resume (PDF/DOCX)
2. Extract text using pdfplumber/python-docx
3. Send to GPT-4 for structured extraction
4. Parse: name, email, phone, skills, experience, education, certifications
5. Store in PostgreSQL with relationships

### JD Analysis Flow
1. Admin uploads JD file or enters text
2. Extract text from file
3. Send to GPT-4 for requirement extraction
4. Extract: required skills, preferred skills, experience, education, keywords
5. Store JD analysis in database

### Matching Flow
1. **Phase 1**: Traditional scoring (fast, keyword-based)
   - Skill overlap matching
   - Experience matching
   - Keyword matching
2. **Phase 2**: AI semantic matching (for top candidates)
   - Send top candidates to GPT-4
   - Semantic understanding of fit
3. **Final Score**: Hybrid calculation
   - 40% skill match
   - 30% experience match
   - 30% semantic match
4. Return top N candidates above threshold

---

## Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Token blacklisting for logout
- File type and size validation
- SQL injection prevention (SQLAlchemy ORM)
- CORS configuration
- Protected API routes
- Admin-only endpoints

---

## Performance Optimizations

- Async/await for database operations
- Background task processing (Celery)
- Database indexing on frequently queried fields
- Traditional scoring filters before expensive AI calls
- Efficient file storage and retrieval

---

## Future Enhancements (Potential)

- Email notifications
- Advanced analytics and reporting
- Integration with ATS systems
- Mobile app
- Multi-language support
- Advanced AI models fine-tuning
- Real-time collaboration features
- Interview scheduling integration

---

## Notes

- **Owner Column**: Currently marked as "TBD" (To Be Determined). Please update with actual feature owners/developers.
- **Database**: All data stored in PostgreSQL
- **File Storage**: Local file system (can be migrated to cloud storage)
- **AI Costs**: Typical JD analysis costs ~$0.01-0.05 per analysis with 100 resumes
- **Scalability**: Designed for horizontal scaling with async operations

---

**Last Updated**: January 2025
**Version**: 1.0.0
**Status**: ✅ Production Ready

