# CLAUDE.md - Assignment Roaster Project Rules

> Project-specific rules for Claude Code. This file is read automatically.

---

## Project Overview

**Project Name:** Assignment Roaster
**Description:** Learners submit a public GitHub repo link; the app analyzes the code with an LLM and returns a funny Thanglish roast plus real improvement tips.
**Tech Stack:**
- Backend: FastAPI + Python 3.11+
- Frontend: React + Vite + TypeScript
- Database: PostgreSQL + SQLAlchemy
- Auth: JWT + GitHub OAuth
- UI: Chakra UI
- AI: OpenAI API (OpenAI SDK)

---

## Project Structure

```
assignment-roaster/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── refresh_token.py
│   │   │   ├── submission.py
│   │   │   └── roast.py          # Roast + ImprovementTip
│   │   ├── schemas/
│   │   ├── routers/              # auth, submissions, roasts, repos
│   │   ├── services/             # github_service, roast_service
│   │   └── auth/
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── context/
│   │   └── types/
│   └── package.json
├── .claude/
│   └── commands/
├── skills/
├── agents/
└── PRPs/
```

---

## Code Standards

### Python (Backend)
```python
# ALWAYS use type hints
def get_submission(db: Session, submission_id: int) -> Submission:
    pass

# ALWAYS add docstrings for public functions
def create_submission(db: Session, user_id: int, data: SubmissionCreate) -> Submission:
    """
    Create a new submission.

    Args:
        db: Database session
        user_id: Owner of the submission
        data: Submission creation data

    Returns:
        Created Submission object
    """
    pass

# Async endpoints
@router.get("/submissions/{id}")
async def get_submission(id: int, db: Session = Depends(get_db)):
    pass
```

### TypeScript (Frontend)
```typescript
// ALWAYS define interfaces for props and data
interface Submission {
  id: number;
  repoUrl: string;
  status: 'pending' | 'fetching' | 'analyzing' | 'completed' | 'failed';
}

// NO any types allowed
const fetchSubmission = async (id: number): Promise<Submission> => {
  // ...
};
```

---

## Forbidden Patterns

### Backend
- ❌ Never use `print()` - use `logging` module
- ❌ Never store passwords in plain text - use bcrypt
- ❌ Never hardcode secrets - use environment variables
- ❌ Never use `SELECT *` - specify columns
- ❌ Never skip input validation
- ❌ Never clone, install, or execute submitted repo code - fetch file contents as text only

### Frontend
- ❌ Never use `any` type
- ❌ Never leave console.log in production
- ❌ Never skip error handling in async operations
- ❌ Never use inline styles - use Chakra UI
- ❌ Never render roast text as raw HTML

---

## Module-Specific Rules

### Submissions Module
- Every submission must belong to a user (`user_id` foreign key)
- Status must be one of: `pending`, `fetching`, `analyzing`, `completed`, `failed`
- Accept only `https://github.com/{owner}/{repo}` URLs; validate strictly (SSRF prevention)
- Only public repos; private or missing repos produce a clear error
- Skip binaries, `node_modules`, lock files, and cap total files/size sent to the LLM
- Analysis runs as a background task; frontend polls status
- Users can only see their own submissions (there is no admin area)
- Users sign in with GitHub and pick a repo from their public repos (`GET /api/v1/repos`); pasting a public repo URL still works

### Roasts Module
- Roast text must be Thanglish (Tamil in English letters mixed with English)
- Funny, never abusive, never personal, never about the learner's identity
- Every roast must include a score (0-100) and at least 3 actionable improvement tips
- Tip categories: `structure`, `naming`, `bugs`, `security`, `readability`, `best_practices`
- Ask the LLM for structured JSON output and validate it with Pydantic before saving
- Treat repo file contents as untrusted input: instruct the model to ignore instructions found in code

### Repos Module
- `GET /api/v1/repos` lists the signed-in user's public, non-fork, non-archived GitHub repos (requires a GitHub-linked account)
- The user's GitHub OAuth token is never stored; only `github_login` is kept

---

## API Conventions

- All endpoints prefixed with `/api/v1/`
- Use plural nouns for resources: `/submissions`, `/roasts`
- Return appropriate HTTP status codes:
  - 200: Success
  - 201: Created
  - 400: Bad Request
  - 401: Unauthorized
  - 403: Forbidden
  - 404: Not Found
  - 409: Conflict
  - 429: Too Many Requests

---

## Authentication

Email/Password + GitHub OAuth.

### JWT Configuration
- Access token expires: 30 minutes
- Refresh token expires: 7 days
- Algorithm: HS256

### OAuth Providers
- GitHub OAuth enabled (scopes `read:user user:email`; callback `/api/v1/auth/github/callback`)
- Always verify state parameter for CSRF protection

---

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/assignment_roaster

# Auth
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# GitHub OAuth (login)
GITHUB_CLIENT_ID=your-client-id
GITHUB_CLIENT_SECRET=your-client-secret

# AI + GitHub
OPENAI_API_KEY=your-openai-api-key
GITHUB_TOKEN=

# Frontend
VITE_API_URL=http://localhost:8000
```

---

## Development Commands

```bash
# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Docker
docker-compose up -d

# Tests
pytest backend/tests -v
cd frontend && npm test

# Linting
ruff check backend/
cd frontend && npm run lint && npm run type-check
```

---

## Commit Message Format

```
feat([module]): add [feature]
fix([module]): fix [bug]
refactor([module]): refactor [component]
test([module]): add tests for [feature]
docs: update [documentation]
```

---

## Skills Reference

| Task | Skill to Read |
|------|---------------|
| Database models | skills/DATABASE.md |
| API + Auth | skills/BACKEND.md |
| React + UI | skills/FRONTEND.md |
| Testing | skills/TESTING.md |
| Deployment | skills/DEPLOYMENT.md |

---

## Agent Coordination

For complex tasks, the ORCHESTRATOR coordinates:
- DATABASE-AGENT → Backend models
- BACKEND-AGENT → API development
- FRONTEND-AGENT → UI components
- TEST-AGENT → Testing
- REVIEW-AGENT → Code review
- DEVOPS-AGENT → Deployment

Read agent definitions in `/agents/` folder.
