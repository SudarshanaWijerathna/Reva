# API Contracts – Reva

## 1. Purpose of This Document

This document defines the **API contracts** between frontend,
backend, and AI services to ensure consistent communication
and independent development.

---

## 2. API Design Principles

- RESTful endpoints
- JSON request/response format
- Stateless interactions
- Clear separation of concerns

---

## 3. Authentication APIs

### POST /auth/register

Registers a new user.

**Request**

```json
{
  "name": "User Name",
  "email": "user@email.com",
  "password": "********"
}
```
