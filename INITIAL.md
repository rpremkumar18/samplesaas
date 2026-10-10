# INITIAL.md - Assignment Roaster Product Definition

> Learners submit a public GitHub repo link and get an AI code review: a funny Thanglish roast plus real improvement tips.

---

## PRODUCT

### Name
Assignment Roaster

### Description
A trainer runs AI content training where learners complete coding assignments and publish them in public GitHub repositories. Assignment Roaster lets each learner paste their repo link. The backend fetches the code, an LLM analyzes it, and the learner gets a roast written in Thanglish (Tamil + English). The roast is funny, but it is paired with genuine, actionable improvement tips. The trainer gets an admin panel to see all learners and submissions.

### Target User
Coding learners (trainees in AI content / coding training programs) who submit assignments as public GitHub repositories.

### Type
- [x] SaaS (Software as a Service)

---

## TECH STACK

### Backend
- [x] FastAPI + Python 3.11+

### Frontend
- [x] React + Vite + TypeScript

### Database
- [x] PostgreSQL + SQLAlchemy

### Authentication
- [x] Email/Password + Google OAuth (JWT)

### UI Framework
- [x] Chakra UI

### Payments
- [ ] None (free for trainees; can be added later)

### AI / External
- [x] OpenAI API (OpenAI SDK) for code analysis and roast generation
- [x] GitHub REST API (public repos) for fetching code

---

## MODULES

### Module 1: Authentication (Required)

**Description:** User authentication and authorization

**Models:**
- User: id, email, hashed_password, full_name, is_active, is_verified, is_admin, oauth_provider, created_at
- RefreshToken: id, user_id, token, expires_at, revoked

**API Endpoints:**
- POST /api/v1/auth/register - Create new account
- POST /api/v1/auth/login - Login with email/password
- POST /api/v1/auth/refresh - Refresh access token
- POST /api/v1/auth/logout - Revoke refresh token
- GET /api/v1/auth/me - Get current user profile
- PUT /api/v1/auth/me - Update profile
- GET /api/v1/auth/google - Start Google OAuth
- GET /api/v1/auth/google/callback - Google OAuth callback

**Frontend Pages:**
- /login - Login page
- /register - Registration page
- /forgot-password - Forgot password page
- /profile - User profile page (protected)

---

### Module 2: Submissions

**Description:** Learners submit public GitHub repo links for review and track their status.

**Models:**
- Submission: id, user_id, repo_url, repo_owner, repo_name, assignment_title, status (pending | fetching | analyzing | completed | failed), error_message, created_at, updated_at

**API Endpoints:**
- POST /api/v1/submissions - Submit a GitHub repo URL (validates it is a public GitHub repo)
- GET /api/v1/submissions - List current user's submissions
- GET /api/v1/submissions/{id} - Get submission details and status
- DELETE /api/v1/submissions/{id} - Delete a submission
- POST /api/v1/submissions/{id}/retry - Retry a failed submission

**Frontend Pages:**
- /submissions/new - Submit repo link form
- /submissions - Submission list with status badges
- /submissions/:id - Submission detail (status, link to roast)

**Business Rules:**
- Only public GitHub repo URLs are accepted (https://github.com/{owner}/{repo})
- Limit files and size fetched per repo (skip binaries, node_modules, lock files)
- Rate limit submissions per user per day

---

### Module 3: Roasts

**Description:** AI analysis of the submitted code, producing a Thanglish roast and real improvement tips.

**Models:**
- Roast: id, submission_id, roast_text (Thanglish), summary, score (0-100), created_at
- ImprovementTip: id, roast_id, category (structure | naming | bugs | security | readability | best_practices), title, description, file_path (nullable)

**API Endpoints:**
- GET /api/v1/roasts/{submission_id} - Get roast and tips for a submission
- GET /api/v1/roasts - List current user's roasts (history)

**Services:**
- GitHubService: fetch repo file tree and contents via GitHub API
- RoastService: build prompt, call OpenAI API, parse structured output (roast, score, tips)

**Frontend Pages:**
- /roasts/:submissionId - Roast result page (Thanglish roast, score, improvement tips list)
- /roasts - Roast history

**Business Rules:**
- Roast must be in Thanglish (Tamil written in English letters mixed with English), funny but never abusive or personal
- Every roast must include at least 3 concrete, actionable improvement tips
- Analysis runs as a background task; frontend polls submission status

---

### Module 4: Dashboard

**Description:** Overview of a learner's activity and progress.

**Frontend Pages:**
- /dashboard - Recent roasts, average score, submission count, score trend
- /settings - User settings and preferences

---

### Module 5: Admin Panel

**Description:** Admin-only (trainer) management interface.

**API Endpoints:**
- GET /api/v1/admin/users - List all users
- PUT /api/v1/admin/users/{id} - Update user status / role
- GET /api/v1/admin/submissions - List all submissions with filters
- GET /api/v1/admin/stats - Platform statistics (users, submissions, average score)

**Frontend Pages:**
- /admin - Admin dashboard (protected, admin only)
- /admin/users - User management
- /admin/submissions - All submissions and roasts

---

## MVP SCOPE

### Must Have (MVP)
- [x] User registration and login (email/password + Google)
- [x] Submit a public GitHub repo link
- [x] AI analysis producing a Thanglish roast plus improvement tips
- [x] View past roasts (history)
- [x] Admin panel to see all users and submissions

### Nice to Have (Post-MVP)
- [ ] Roast intensity levels (mild / medium / savage)
- [ ] Email notification when a roast is ready
- [ ] Leaderboard across learners
- [ ] Share roast as an image/link
- [ ] Re-submit same repo and compare score improvement
- [ ] Payments

---

## ACCEPTANCE CRITERIA

### Authentication
- [ ] User can register with email/password
- [ ] User can login with email/password
- [ ] User can login with Google
- [ ] JWT tokens work correctly with refresh
- [ ] Protected routes redirect to login
- [ ] Admin routes reject non-admin users (403)

### Submissions
- [ ] User can submit a valid public GitHub repo URL
- [ ] Invalid, non-GitHub, or private repo URLs are rejected with a clear error
- [ ] User sees only their own submissions
- [ ] Status updates from pending to completed (or failed) and is visible in the UI
- [ ] Failed submissions can be retried

### Roasts
- [ ] Completed submission has a roast written in Thanglish
- [ ] Roast includes a score and at least 3 improvement tips
- [ ] Roast history lists all of the user's past roasts
- [ ] Roast content is not abusive or personally insulting

### Admin
- [ ] Admin can list all users and submissions
- [ ] Admin can deactivate a user
- [ ] Admin stats endpoint returns accurate counts

### Quality
- [ ] All API endpoints documented in OpenAPI
- [ ] Backend test coverage 80%+ (GitHub and Claude calls mocked)
- [ ] Frontend TypeScript strict mode passes
- [ ] Docker builds and runs successfully

---

## SPECIAL REQUIREMENTS

### Security
- [x] Rate limiting on auth and submission endpoints
- [x] Input validation on all endpoints (strict GitHub URL validation to prevent SSRF)
- [x] SQL injection prevention
- [x] XSS prevention (render roast text safely)
- [x] CSRF protection (OAuth state parameter)
- [x] Treat repo code as untrusted: never execute it, and guard against prompt injection from file contents

### Integrations
- [ ] Email service for notifications (post-MVP)
- [ ] Payments
- [ ] File upload service
- [x] OpenAI API (code analysis)
- [x] GitHub API (repo fetching)

---

## AGENTS

> These 6 agents will build your product in parallel:

| Agent | Role | Works On |
|-------|------|----------|
| DATABASE-AGENT | Creates all models and migrations | User, RefreshToken, Submission, Roast, ImprovementTip |
| BACKEND-AGENT | Builds API endpoints and services | Auth, submissions, roasts, admin, GitHub and Claude services |
| FRONTEND-AGENT | Creates UI pages and components | Auth pages, submit form, roast page, dashboard, admin |
| DEVOPS-AGENT | Sets up Docker, CI/CD, environments | Infrastructure |
| TEST-AGENT | Writes unit and integration tests | All code |
| REVIEW-AGENT | Security and code quality audit | All code |

---

# READY?

```bash
/generate-prp INITIAL.md
```

Then:

```bash
/execute-prp PRPs/assignment-roaster-prp.md
```
