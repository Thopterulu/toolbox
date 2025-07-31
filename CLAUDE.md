# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a toolbox repository containing various utility scripts and tools:

- **Python scripts**: PDF manipulation, Google Calendar integration, Clockify time tracking, misc utilities
- **Go API client**: Google Keep API integration for notes retrieval
- **Mixed language support**: Python (3.12+) and Go (1.23+)

## Development Commands

### Task Runner (Just)
The project uses `just` as the primary task runner. Key commands:

```bash
# Run default Clockify daily schedule
just

# Remove night entries from last 2 weeks
just remove_nights

# Autofill specific date (YYYY-MM-DD)
just autofill 2024-01-15

# Autofill current week (Mon-Fri)
just autofill_week

# Autofill date range
just autofill_range 2024-01-01 2024-01-05
```

### Python Environment
- Uses `uv` for dependency management
- Python 3.12+ required
- Install dependencies: `uv sync`
- Optional Google Calendar dependencies: `uv sync --extra google_calendar`

### Go Development (gkeep_api/)
```bash
# Build and run
cd gkeep_api
go run cmd/main.go

# Install dependencies
go mod tidy
```

## Architecture

### Python Scripts Structure
- **`timerz/clockify.py`**: Main Clockify integration with timezone-aware scheduling, supports multiple actions via `CLOCKIFY_ACTION` env var
- **`google_calendar/`**: Google Calendar API integration for event management
- **`pdf/`**: PDF manipulation utilities (concatenation, watermarking)
- **`misc/`**: Standalone utility functions

### Go API Client (gkeep_api/)
Standard Go project structure:
- **`cmd/main.go`**: Application entry point
- **`internal/api/`**: Google Keep API client implementation with OAuth2
- **`internal/models/`**: Data structures for notes
- **`configs/`**: Configuration management with environment variables

### Key Environment Variables
- **Clockify**: `API_KEY`, `WORKSPACE_ID`, `USER_ID`
- **Google APIs**: Requires OAuth2 credentials and token files
- **Timezone**: Uses `Europe/Paris` by default in Clockify scripts

## Important Implementation Details

- **Clockify script**: Handles timezone conversion (Europe/Paris ↔ UTC), random scheduling for realistic time entries, automatic lunch break insertion
- **Go Keep API**: Uses OAuth2 flow with context-based operations
- **PDF scripts**: Selenium-based automation for government watermarking service
- **Google Calendar**: Full OAuth2 integration with credential management

## Dependencies Management

- Python: Dependencies defined in `pyproject.toml`, managed with `uv`
- Go: Standard `go.mod` with minimal external dependencies (godotenv, oauth2)