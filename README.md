# Personal Task Management Agent 🤖📅

A conversational AI agent built with LangChain and Chainlit that helps users manage their personal tasks and schedules. The agent can create, update, and read tasks while handling timezone conversions automatically to provide contextually relevant scheduling recommendations.

## Features ✨

- **Conversational Task Management**: Natural language interface for managing tasks
- **Timezone-Aware Scheduling**: All tasks stored in UTC with automatic conversion to user's local timezone
- **CRUD Operations**: Create, read, update tasks through natural conversation
- **User Authentication**: Secure password-based authentication system
- **Persistent Storage**: PostgreSQL database with proper data persistence
- **Docker Deployment**: Easy deployment using Docker Compose

## Tech Stack 🛠️

- **Backend**: Python 3.10, LangChain, SQLAlchemy
- **Frontend**: Chainlit web interface
- **Database**: PostgreSQL 14
- **LLM**: Azure OpenAI GPT-4
- **Authentication**: Password-based with bcrypt hashing
- **Deployment**: Docker & Docker Compose

## Project Structure 📁

```
├── app/
│   ├── auth.py          # Authentication utilities
│   ├── db.py            # Database configuration
│   └── models.py        # SQLAlchemy models
├── scripts/
│   └── init-db.sh       # Database initialization script
├── assets/
│   └── test.css         # Custom styling
├── chainlit_app.py      # Main Chainlit application
├── main.ipynb          # Development notebook
├── docker-compose.yaml  # Docker services configuration
├── Dockerfile          # Application container
├── pyproject.toml      # Python dependencies
├── chainlit.md         # Welcome screen content
└── .chainlit/          # Chainlit configuration
```

## Quick Start 🚀

### Prerequisites

- Docker and Docker Compose installed
- Environment variables configured 

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd adv_camp
```

### 2. Environment Setup

Create a `.env` file in the root directory with the following variables:

```env
# Database Configuration
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=postgres
DB_PORT=5432
DB_NAME=postgres
CHAINLIT_DB=chainlit_db

# Docker Configuration
DOCKER_CONTAINER=postgres_container
HOST_PORT=5432
POSTGRES_SCHEMA=postgres
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin_password
PGADMIN_PORT=5050

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_ENDPOINT=your_endpoint

# Database URLs
DATABASE_URL=postgresql://postgres:your_password@postgres:5432/postgres
ASYNC_DATABASE_URL=postgresql+asyncpg://postgres:your_password@postgres:5432/postgres
ASYNC_CHAINLIT_DB_URL=postgresql+asyncpg://postgres:your_password@postgres:5432/chainlit_db

# Chainlit Configuration
CHAINLIT_AUTH_SECRET=your_secret_key
```

### 3. Deploy with Docker

```bash
docker-compose up -d
```

### 4. Access the Application

- **Chainlit Interface**: http://localhost:8000
- **PgAdmin**: http://localhost:5050

### 5. Login with Test User

A test user is pre-configured for immediate testing:

```
Email: test@example.com
Password: password123
```

Use these credentials to log in and start managing your tasks right away!

## Usage Examples 💬

Once logged in, you can interact with the agent using natural language:

### Creating Tasks
```
"I need to schedule a team meeting tomorrow at 2 PM for 2 hours"
"Add a doctor appointment on Friday at 10 AM"
"Create a task for project deadline next week"
```

### Reading Tasks
```
"What are my tasks for today?"
"Show me my schedule for next week"
"What meetings do I have this afternoon?"
```

### Updating Tasks
```
"Move my 2 PM meeting to 3 PM"
"Change the project deadline to next Friday"
"Update the team meeting description"
```

## Database Schema 📊

### Users Table
- `id`: UUID primary key
- `username`: Unique username
- `email`: Unique email address
- `hashed_password`: Bcrypt hashed password
- `timezone`: IANA timezone identifier
- `bio`: Optional user biography
- `created_at`, `updated_at`: Timestamps

### Tasks Table
- `task_id`: UUID primary key
- `task_name`: Task title
- `task_description`: Optional description
- `user_id`: Foreign key to users
- `start_time_utc`, `end_time_utc`: UTC timestamps
- `original_timezone`: User's timezone when created
- `priority`: Enum (LOW, MEDIUM, HIGH)
- `status`: Enum (ACTIVE, COMPLETED)
- `recurrence_rule`: RFC 5545 RRULE for repeating tasks

## Configuration ⚙️

### Timezone Support

The application supports multiple timezones with automatic conversion:
- All times stored in UTC in the database
- User's local timezone specified in their profile
- Automatic conversion for display and input

### Agent Configuration

The LangChain agent is configured with:
- **System Prompt**: Defines agent behavior and protocols
- **Tools**: `get_user_tasks`, `add_task`, `update_task`
- **Memory**: Conversation buffer for context retention
- **Approval Protocol**: User confirmation required for modifications

## Security Considerations 🔒

- Passwords are hashed using bcrypt
- Database credentials stored in environment variables
- SQL injection protection through SQLAlchemy ORM
- Task modification requires explicit user approval
- User authentication required for all operations

## License 📝

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Troubleshooting 🔧

### Common Issues

1. **Database Connection Errors**
   - Ensure PostgreSQL container is running
   - Check environment variables are correctly set
   - Verify database URLs in `.env`

2. **Authentication Issues**
   - Check `CHAINLIT_AUTH_SECRET` is set
   - Verify user credentials in database
   - Ensure password hashing is working correctly

3. **Timezone Issues**
   - Verify user timezone is set correctly
   - Check IANA timezone identifiers are valid
   - Ensure UTC conversion functions are working

### Logs

View application logs:
```bash
docker-compose logs motiva
docker-compose logs postgres
```