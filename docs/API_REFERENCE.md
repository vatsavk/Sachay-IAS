# SANCHAY IAS - API Reference

## Base URL

```
http://localhost:8001
```

---

## Authentication

Currently uses role-based access (built-in):
- `advisor` - Full access
- `client` - Limited access
- `admin` - Administrative access

Future: JWT authentication planned

---

## Health & Status Endpoints

### Health Check

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "ok",
  "service": "SANCHAY IAS API",
  "version": "2.0.0"
}
```

### Server Status

**Endpoint**: `GET /status`

**Response**:
```json
{
  "status": "running",
  "version": "2.0.0",
  "host": "0.0.0.0",
  "port": 8001,
  "cors_origins": ["http://localhost:3000", "http://localhost:5000"]
}
```

---

## User Management

### List All Users

**Endpoint**: `GET /users`

**Response**:
```json
[
  {
    "user_id": 1,
    "name": "Dr. Arvind Sharma",
    "email": "arvind@example.com",
    "phone": "+91-9999999999",
    "role": "advisor",
    "status": "active",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

### Get User by ID

**Endpoint**: `GET /users/{user_id}`

**Parameters**:
- `user_id` (integer) - User ID

**Response**:
```json
{
  "user_id": 1,
  "name": "Dr. Arvind Sharma",
  "email": "arvind@example.com",
  "phone": "+91-9999999999",
  "role": "advisor",
  "status": "active",
  "created_at": "2024-01-15T10:30:00"
}
```

### Create User

**Endpoint**: `POST /users`

**Request Body**:
```json
{
  "name": "Dr. Arvind Sharma",
  "email": "arvind@example.com",
  "phone": "+91-9999999999",
  "role": "advisor",
  "status": "active"
}
```

**Response**:
```json
{
  "user_id": 1,
  "message": "User created successfully"
}
```

**Errors**:
- `400` - Invalid input or duplicate email
- `500` - Server error

---

## Client Management

### List All Clients

**Endpoint**: `GET /clients`

**Response**:
```json
[
  {
    "client_id": 1,
    "user_id": 2,
    "advisor_id": 1,
    "dob": "1980-05-15",
    "income": 2500000,
    "net_worth": 15000000,
    "occupation": "Software Engineer",
    "onboarding_date": "2023-01-01"
  }
]
```

### Get Client by ID

**Endpoint**: `GET /clients/{client_id}`

**Parameters**:
- `client_id` (integer) - Client ID

**Response**:
```json
{
  "client_id": 1,
  "user_id": 2,
  "advisor_id": 1,
  "dob": "1980-05-15",
  "income": 2500000,
  "net_worth": 15000000,
  "occupation": "Software Engineer",
  "onboarding_date": "2023-01-01"
}
```

### Create Client

**Endpoint**: `POST /clients`

**Request Body**:
```json
{
  "user_id": 2,
  "advisor_id": 1,
  "dob": "1980-05-15",
  "income": 2500000,
  "net_worth": 15000000,
  "occupation": "Software Engineer",
  "onboarding_date": "2023-01-01"
}
```

**Response**:
```json
{
  "client_id": 1,
  "message": "Client created successfully"
}
```

---

## Goal Management

### List All Goals

**Endpoint**: `GET /goals`

**Response**:
```json
[
  {
    "goal_id": 1,
    "client_id": 1,
    "goal_type": "Retirement",
    "target_amount": 5000000,
    "current_corpus": 1200000,
    "target_date": "2040-12-31",
    "monthly_sip": 50000,
    "created_at": "2024-01-15T10:30:00"
  }
]
```

### Create Goal

**Endpoint**: `POST /goals`

**Request Body**:
```json
{
  "client_id": 1,
  "goal_type": "Retirement",
  "target_amount": 5000000,
  "current_corpus": 1200000,
  "target_date": "2040-12-31",
  "monthly_sip": 50000
}
```

**Response**:
```json
{
  "goal_id": 1,
  "message": "Goal created successfully"
}
```

---

## Dashboard & Analytics

### Dashboard Summary

**Endpoint**: `GET /dashboard`

**Response**:
```json
{
  "total_clients": 28,
  "total_goals": 45,
  "total_aum": "₹145.2 Cr",
  "tasks_pending": 5
}
```

### Tasks List

**Endpoint**: `GET /tasks`

**Response**:
```json
{
  "tasks": [
    {
      "task_id": 1,
      "title": "Call Rahul Desai",
      "due_date": "2024-02-01",
      "status": "pending"
    }
  ]
}
```

### Compliance Status

**Endpoint**: `GET /compliance`

**Response**:
```json
{
  "status": "compliant",
  "items": [
    {
      "item_id": 1,
      "type": "KYC",
      "client_id": 1,
      "status": "completed"
    }
  ]
}
```

### Reports List

**Endpoint**: `GET /reports`

**Response**:
```json
{
  "reports": [
    {
      "report_id": 1,
      "type": "Portfolio Review",
      "client_id": 1,
      "generated_at": "2024-01-15T10:30:00"
    }
  ]
}
```

### Team Members

**Endpoint**: `GET /team`

**Response**:
```json
{
  "team": [
    {
      "advisor_id": 1,
      "name": "Dr. Arvind Sharma",
      "role": "Lead Advisor",
      "clients_managed": 15
    }
  ]
}
```

---

## Error Responses

### 400 - Bad Request

```json
{
  "detail": "Invalid input: email format incorrect"
}
```

### 404 - Not Found

```json
{
  "detail": "User not found"
}
```

### 500 - Server Error

```json
{
  "error": "Internal server error",
  "status": "error"
}
```

---

## Rate Limiting

Currently no rate limiting. Recommended to add for production:
- 100 requests per minute per IP

---

## CORS Headers

Configured CORS origins (from `.env` `CORS_ORIGINS`):
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

---

## Pagination (Future)

Planning to add pagination for large datasets:
```
GET /clients?page=1&per_page=20
```

---

## Filtering & Search (Future)

Planning advanced filtering:
```
GET /clients?advisor_id=1&status=active
GET /goals?client_id=1&status=at_risk
```

---

## Webhooks (Future)

Planning webhook support for:
- Client created
- Goal status changed
- Transaction processed
- Compliance alerts

---

## Rate Limiting Headers (When Enabled)

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1703079600
```

---

**API Version**: 2.0.0
**Last Updated**: 2024
