# Event Management API System

A robust Flask-based REST API designed for comprehensive event scheduling and management with automated persistence and notification capabilities.

## System Capabilities

### Primary Functionality
- Event Registration**: Add new events specifying title, description, start/end times
- Event Retrieval**: Display all scheduled events chronologically ordered
- Event Modification**: Edit existing event properties and timing
- Event Removal**: Delete unwanted events from the system
- Data Persistence**: Automatic JSON-based storage with session recovery

### Enhanced Features
- Testing Framework**: Complete pytest-based validation suite
- Alert System**: Automated background notifications for imminent events
- Query Functionality**: Text-based search across event titles and descriptions
- Exception Management**: Robust error handling with informative responses
- RESTful Design**: Standards-compliant HTTP methods and status codes

## System Requirements & Deployment

### Technical Prerequisites
- Python runtime 3.7 or higher
- Package installer (pip)

### Environment Configuration
1. Initialize project workspace
```bash
git clone <repository-url>
cd event-management-api
```

2. Configure isolated Python environment
```bash
python -m venv event_env
source event_env/bin/activate  # Windows: event_env\Scripts\activate
```

3. Install required packages
```bash
pip install flask pytest
```

## Application Execution

### Server Initialization
```bash
python app.py
```

Application launches at `http://localhost:5000`

### Automated Services
- **Notification Monitor**: Continuously scans for events approaching within 60 minutes, providing console alerts every minute

## REST API Documentation

### System Status Verification
```
GET /health
```
**Returns:**
```json
{
  "status": "healthy",
  "timestamp": "2024-06-29T10:30:00"
}
```

### Event Registration
```
POST /events
Content-Type: application/json
```
**Payload:**
```json
{
  "title": "Project Standup",
  "description": "Daily team coordination meeting",
  "start_time": "2024-12-01 09:00:00",
  "end_time": "2024-12-01 09:30:00",
  "recurring": "daily"
}
```
**Success Response (201):**
```json
{
  "message": "Event registered successfully",
  "event": {
    "id": 1,
    "title": "Project Standup",
    "description": "Daily team coordination meeting",
    "start_time": "2024-12-01T09:00:00",
    "end_time": "2024-12-01T09:30:00",
    "recurring": "daily",
    "created_at": "2024-06-29T10:30:00"
  }
}
```

### Event Collection Retrieval
```
GET /events
GET /events?sort_by=start_time
```
**Response Structure:**
```json
{
  "events": [
    {
      "id": 1,
      "title": "Project Standup",
      "description": "Daily team coordination meeting",
      "start_time": "2024-12-01T09:00:00",
      "end_time": "2024-12-01T09:30:00",
      "recurring": "daily",
      "created_at": "2024-06-29T10:30:00"
    }
  ],
  "count": 1
}
```

### Individual Event Access
```
GET /events/{event_id}
```
**Response (200):**
```json
{
  "event": {
    "id": 1,
    "title": "Project Standup",
    "description": "Daily team coordination meeting",
    "start_time": "2024-12-01T09:00:00",
    "end_time": "2024-12-01T09:30:00",
    "recurring": "daily"
  }
}
```

### Event Modification
```
PUT /events/{event_id}
Content-Type: application/json
```
**Partial Update Payload:**
```json
{
  "title": "Revised Meeting Title",
  "description": "Modified meeting description"
}
```
**Confirmation Response (200):**
```json
{
  "message": "Event updated successfully",
