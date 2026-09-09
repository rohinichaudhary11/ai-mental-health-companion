## MongoDB Schema Design (Reference)

This document describes recommended MongoDB collections for a production deployment
of the AI-Powered Personalized Mental Health Companion. The current demo uses
in-memory stores; these schemas are meant as a blueprint when wiring MongoDB.

### 1. `users`

```json
{
  "_id": "ObjectId",
  "email": "string",
  "password_hash": "string",       // Argon2 / bcrypt hash
  "full_name": "string",
  "created_at": "ISODate",
  "last_login_at": "ISODate",
  "preferences": {
    "timezone": "string",
    "dark_mode": "boolean",
    "notification_channel": "email | push | none"
  }
}
```

### 2. `mood_logs`

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "mood": "very_low | low | neutral | high | very_high",
  "emoji": "string",
  "note": "string",
  "created_at": "ISODate"
}
```

Indexes:
- `{ user_id: 1, created_at: -1 }`

### 3. `journal_entries`

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "title": "string",
  "content_encrypted": "Binary",   // Encrypted payload
  "created_at": "ISODate",
  "last_modified_at": "ISODate",
  "emotion_snapshot": {
    "label": "string",
    "confidence": "number",
    "probabilities": { "joy": 0.1, "sadness": 0.2 }
  }
}
```

Indexes:
- `{ user_id: 1, created_at: -1 }`

### 4. `emotion_insights`

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "from_date": "ISODate",
  "to_date": "ISODate",
  "top_emotions": { "sadness": 5, "joy": 2 },
  "average_confidence": "number",
  "notes": ["string"],
  "generated_at": "ISODate"
}
```

### 5. `symptom_alerts`

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "input_text": "string",
  "detected_conditions": [
    {
      "name": "string",
      "likelihood": "string",
      "explanation": "string"
    }
  ],
  "crisis_detected": "boolean",
  "created_at": "ISODate",
  "handled_by_human": "boolean",
  "handled_at": "ISODate"
}
```

Indexes:
- `{ user_id: 1, created_at: -1 }`
- `{ crisis_detected: 1, created_at: -1 }`

### 6. `medical_support_requests`

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "input_text": "string",
  "location": {
    "lat": "number",
    "lon": "number",
    "raw": "string"
  },
  "detected_conditions": [
    {
      "name": "string",
      "likelihood": "string"
    }
  ],
  "nearby_results": [
    {
      "name": "string",
      "address": "string",
      "contact_number": "string",
      "distance_km": "number",
      "type": "hospital | clinic | doctor"
    }
  ],
  "created_at": "ISODate"
}
```

### Notes on Security & Privacy

- Store **only the minimum data** needed to provide value.
- Encrypt sensitive fields such as journal content using an application-level
  encryption key (e.g., AES-GCM) before writing to MongoDB.
- Use separate environments and databases for dev/staging/production.
- Avoid logging raw journal or symptom text to application logs.

