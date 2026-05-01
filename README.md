# Team Task Manager

A production-ready full-stack task management application with role-based access control.

## Features

- **Authentication System**: JWT-based auth with bcrypt password hashing
- **Role-Based Access Control**: Admin and Member roles
- **Project Management**: Create projects, add/remove members
- **Task Management**: Create, assign, and track tasks with status filtering
- **Dashboard**: Overview with task statistics and overdue alerts

## Tech Stack

- **Backend**: Python Flask (REST API)
- **Frontend**: HTML, CSS, Vanilla JavaScript
- **Database**: PostgreSQL (SQLite for local dev)
- **Authentication**: JWT tokens

## Project Structure

```
team-task-manager/
├── backend/
│   ├── app/
│   │   ├── models/       # Database models
│   │   ├── routes/       # API endpoints
│   │   └── utils/        # Helper functions
│   ├── config.py         # Configuration
│   ├── run.py            # Application entry point
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── index.html        # Login/Signup
│   ├── dashboard.html   # Main dashboard
│   ├── projects.html     # Projects page
│   ├── tasks.html        # Tasks page
│   ├── css/
│   │   └── style.css     # Styles
│   └── js/
│       ├── auth.js       # Auth handling
│       ├── api.js        # API calls
│       └── app.js        # Main app logic
├── Procfile              # Railway deployment
├── runtime.txt           # Python version
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.10+
- PostgreSQL (optional for local dev)

### Local Development

1. **Create virtual environment**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set environment variables**:
```bash
# On Windows (CMD)
set FLASK_APP=run.py
set FLASK_ENV=development
set SECRET_KEY=your-secret-key
set DATABASE_URL=sqlite:///teamtask.db

# On Windows (PowerShell)
$env:FLASK_APP="run.py"
$env:FLASK_ENV="development"
$env:SECRET_KEY="your-secret-key"
$env:DATABASE_URL="sqlite:///teamtask.db"
```

4. **Run the application**:
```bash
cd backend
python run.py
```

5. **Access the app**:
- Frontend: http://localhost:5000
- API: http://localhost:5000/api

### Railway Deployment

1. **Push to GitHub**

2. **Create Railway project**:
   - Go to railway.app
   - Create new project from GitHub repo

3. **Add environment variables**:
   ```
   SECRET_KEY=<generate-random-key>
   DATABASE_URL=<postgresql-connection-string>
   FLASK_ENV=production
   ```

4. **Deploy**: Railway will automatically detect Python and deploy

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Register new user |
| POST | /api/auth/login | Login user |
| GET | /api/auth/me | Get current user |

### Projects
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/projects | List all projects |
| POST | /api/projects | Create project (Admin) |
| GET | /api/projects/:id | Get project details |
| PUT | /api/projects/:id | Update project |
| DELETE | /api/projects/:id | Delete project |
| POST | /api/projects/:id/members | Add member to project |
| DELETE | /api/projects/:id/members/:userId | Remove member |

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/projects/:projectId/tasks | List tasks |
| POST | /api/projects/:projectId/tasks | Create task |
| PUT | /api/tasks/:id | Update task |
| DELETE | /api/tasks/:id | Delete task |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/dashboard/stats | Get dashboard statistics |

## Demo Credentials

After registration, users are assigned "Member" role by default. To get admin access:

1. Register a new account
2. Manually update the role in database to "admin"

Or use the first registered user as admin.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| SECRET_KEY | JWT secret key | random-string |
| DATABASE_URL | Database connection | sqlite:///teamtask.db |
| FLASK_ENV | Environment | development |
| FLASK_APP | Application module | run.py |

## Screenshots

The application includes:
- Clean login/signup pages
- Dashboard with task statistics
- Project management interface
- Task creation and tracking
- Overdue task highlighting