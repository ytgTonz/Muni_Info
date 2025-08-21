# Muni-Info API Reference v1.0

## Base URL
```
http://localhost:5000/api/v1
```

## Authentication
All API endpoints require authentication via API key in the header:
```
X-API-Key: demo-api-key
```

## Response Format
All responses follow this format:
```json
{
  "status": "success|error",
  "data": {},
  "message": "Optional message",
  "pagination": {}  // For paginated endpoints
}
```

## Endpoints

### Health Check
```http
GET /api/v1/health
```
Returns API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-08-20T10:30:00Z",
  "version": "1.0.0",
  "service": "Muni-Info API"
}
```

### Authentication

#### Get Auth Token
```http
POST /api/v1/auth/token
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "token": "token-user123-timestamp",
  "user": {
    "id": "user_id",
    "username": "admin",
    "role": "admin",
    "municipality": "City of Cape Town"
  }
}
```

### Complaints

#### List Complaints
```http
GET /api/v1/complaints?page=1&per_page=20&status=submitted&priority=high&municipality=Cape%20Town
```

**Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20, max: 100)
- `status` (optional): Filter by status (submitted, in_progress, under_review, resolved, closed)
- `priority` (optional): Filter by priority (low, medium, high, urgent)
- `municipality` (optional): Filter by municipality

**Response:**
```json
{
  "items": [
    {
      "reference_id": "MI-2024-123456",
      "sender": "+27123456789",
      "complaint_type": "Water",
      "description": "No water supply since yesterday",
      "status": "submitted",
      "priority": "high",
      "timestamp": "2024-08-20T08:30:00Z",
      "updated_at": "2024-08-20T08:30:00Z",
      "location_info": {
        "province": "Western Cape",
        "district": "City of Cape Town",
        "municipality": "Cape Town"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8,
    "has_prev": false,
    "has_next": true
  }
}
```

#### Get Specific Complaint
```http
GET /api/v1/complaints/{reference_id}
```

**Response:**
```json
{
  "reference_id": "MI-2024-123456",
  "sender": "+27123456789",
  "complaint_type": "Water",
  "description": "Detailed complaint description",
  "status": "in_progress",
  "priority": "high",
  "timestamp": "2024-08-20T08:30:00Z",
  "updated_at": "2024-08-20T10:15:00Z",
  "image_urls": ["data/media/20240820_083000_abc123.jpg"],
  "resolution_notes": "Technician dispatched to area",
  "location_info": {
    "latitude": -33.9249,
    "longitude": 18.4241,
    "province": "Western Cape"
  }
}
```

#### Create Complaint
```http
POST /api/v1/complaints
Content-Type: application/json

{
  "sender": "+27123456789",
  "complaint_type": "Electricity",
  "description": "Power outage in my area since this morning",
  "priority": "high",
  "location_info": {
    "latitude": -33.9249,
    "longitude": 18.4241
  }
}
```

**Response:**
```json
{
  "message": "Complaint created successfully",
  "complaint": {
    "reference_id": "MI-2024-789012",
    "status": "submitted",
    "priority": "high",
    // ... full complaint object
  }
}
```

#### Update Complaint Status
```http
PUT /api/v1/complaints/{reference_id}/status
Content-Type: application/json

{
  "status": "resolved",
  "notes": "Issue fixed by replacing faulty transformer"
}
```

**Response:**
```json
{
  "message": "Status updated successfully",
  "complaint": {
    "reference_id": "MI-2024-123456",
    "status": "resolved",
    "updated_at": "2024-08-20T14:30:00Z",
    // ... updated complaint object
  }
}
```

#### Get Complaint Statistics
```http
GET /api/v1/complaints/stats?municipality=Cape%20Town&days=30
```

**Parameters:**
- `municipality` (optional): Filter by municipality
- `days` (optional): Number of days to include (default: 30)

**Response:**
```json
{
  "overview": {
    "total": 1250,
    "by_status": {
      "submitted": 45,
      "in_progress": 123,
      "under_review": 67,
      "resolved": 945,
      "closed": 70
    },
    "by_priority": {
      "low": 234,
      "medium": 678,
      "high": 289,
      "urgent": 49
    },
    "by_type": {
      "Water": 345,
      "Electricity": 289,
      "Sanitation": 234,
      "Roads": 198,
      "Other": 184
    }
  },
  "recent_days": 30,
  "daily_timeline": {
    "2024-08-01": 12,
    "2024-08-02": 8,
    // ... daily counts
  },
  "total_recent": 387
}
```

### Location Services

#### Identify Location
```http
POST /api/v1/location/identify
Content-Type: application/json

{
  "latitude": -33.9249,
  "longitude": 18.4241
}
```

**Response:**
```json
{
  "latitude": -33.9249,
  "longitude": 18.4241,
  "province": "Western Cape",
  "district": "City of Cape Town",
  "municipality": "Cape Town"
}
```

### Announcements

#### List Announcements
```http
GET /api/v1/announcements?municipality=Cape%20Town&limit=10
```

**Parameters:**
- `municipality` (optional): Filter by municipality
- `limit` (optional): Number of announcements (default: 50, max: 100)

**Response:**
```json
{
  "announcements": [
    {
      "announcement_id": "ANN-20240820143000",
      "title": "Scheduled Water Maintenance",
      "content": "Water supply will be interrupted on Friday...",
      "municipality": "Cape Town",
      "author": "Water Department",
      "announcement_type": "maintenance",
      "priority": "high",
      "is_active": true,
      "created_at": "2024-08-20T14:30:00Z",
      "expires_at": "2024-08-25T18:00:00Z",
      "areas_affected": ["Ward 1", "Ward 2"],
      "contact_info": "+27 21 xxx xxxx"
    }
  ],
  "total": 5
}
```

#### Create Announcement
```http
POST /api/v1/announcements
Content-Type: application/json

{
  "title": "Emergency Road Closure",
  "content": "Main Road will be closed due to emergency repairs",
  "municipality": "Cape Town",
  "author": "Roads Department",
  "type": "emergency",
  "priority": "urgent",
  "expires_in_days": 3,
  "areas_affected": ["CBD", "Green Point"],
  "contact_info": "+27 21 xxx xxxx"
}
```

**Response:**
```json
{
  "message": "Announcement created successfully",
  "announcement": {
    "announcement_id": "ANN-20240820150000",
    // ... full announcement object
  }
}
```

### Service Ratings

#### Submit Rating
```http
POST /api/v1/ratings
Content-Type: application/json

{
  "service_type": "Water",
  "rating": 4,
  "municipality": "Cape Town",
  "user_phone": "+27123456789",
  "comment": "Generally good service, but occasional disruptions",
  "is_anonymous": false
}
```

**Response:**
```json
{
  "message": "Rating submitted successfully",
  "rating": {
    "rating_id": "RAT-20240820151500",
    "service_type": "Water",
    "rating": 4,
    "municipality": "Cape Town",
    "created_at": "2024-08-20T15:15:00Z"
  }
}
```

#### Get Rating Summary
```http
GET /api/v1/ratings/summary?municipality=Cape%20Town
```

**Response:**
```json
{
  "municipality": "Cape Town",
  "service_ratings": {
    "Water": {
      "average": 4.2,
      "count": 245,
      "distribution": {
        "1": 12,
        "2": 18,
        "3": 45,
        "4": 89,
        "5": 81
      }
    },
    "Electricity": {
      "average": 3.8,
      "count": 198,
      "distribution": {
        "1": 15,
        "2": 23,
        "3": 67,
        "4": 78,
        "5": 15
      }
    }
    // ... other services
  }
}
```

### Webhooks

#### External Complaint Update
```http
POST /api/v1/webhooks/complaint-update
Content-Type: application/json

{
  "reference_id": "MI-2024-123456",
  "status": "in_progress",
  "notes": "Technician assigned to case",
  "system": "Municipal ERP System"
}
```

**Response:**
```json
{
  "message": "Complaint updated successfully",
  "reference_id": "MI-2024-123456",
  "status": "in_progress"
}
```

### Error Responses

#### 400 Bad Request
```json
{
  "error": "Latitude and longitude are required"
}
```

#### 401 Unauthorized
```json
{
  "error": "API key required"
}
```

#### 404 Not Found
```json
{
  "error": "Complaint not found"
}
```

#### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

## Rate Limits
- **Default**: 1000 requests per hour per API key
- **Burst**: Up to 10 requests per second

## Data Validation

### Complaint Types
- `Water`
- `Electricity`
- `Sanitation`
- `Roads`
- `Other`

### Priority Levels
- `low`
- `medium`
- `high`
- `urgent`

### Status Values
- `submitted`
- `in_progress`
- `under_review`
- `resolved`
- `closed`

### Announcement Types
- `general`
- `maintenance`
- `service_disruption`
- `event`
- `emergency`

## SDKs & Examples

### Python Example
```python
import requests

# Configuration
API_BASE = "http://localhost:5000/api/v1"
API_KEY = "demo-api-key"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# Create complaint
complaint_data = {
    "sender": "+27123456789",
    "complaint_type": "Water",
    "description": "No water supply",
    "priority": "high"
}

response = requests.post(
    f"{API_BASE}/complaints",
    json=complaint_data,
    headers=HEADERS
)

if response.status_code == 201:
    complaint = response.json()["complaint"]
    print(f"Complaint created: {complaint['reference_id']}")
else:
    print(f"Error: {response.json()['error']}")

# Check complaint status
reference_id = "MI-2024-123456"
response = requests.get(
    f"{API_BASE}/complaints/{reference_id}",
    headers=HEADERS
)

if response.status_code == 200:
    complaint = response.json()
    print(f"Status: {complaint['status']}")
```

### JavaScript Example
```javascript
const API_BASE = 'http://localhost:5000/api/v1';
const API_KEY = 'demo-api-key';

const headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
};

// Submit rating
async function submitRating(serviceType, rating, municipality, userPhone, comment) {
    const response = await fetch(`${API_BASE}/ratings`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            service_type: serviceType,
            rating: rating,
            municipality: municipality,
            user_phone: userPhone,
            comment: comment
        })
    });
    
    if (response.ok) {
        const result = await response.json();
        console.log('Rating submitted:', result.rating.rating_id);
    } else {
        const error = await response.json();
        console.error('Error:', error.error);
    }
}

// Get statistics
async function getStats() {
    const response = await fetch(`${API_BASE}/complaints/stats`, {
        headers: headers
    });
    
    if (response.ok) {
        const stats = await response.json();
        console.log('Total complaints:', stats.overview.total);
        console.log('Resolution rate:', 
            Math.round(stats.overview.by_status.resolved / stats.overview.total * 100) + '%'
        );
    }
}
```

## Testing
Use the provided API endpoints for testing integration with the Muni-Info system. All endpoints support CORS for web-based applications.

## Support
For API support and integration assistance, contact the development team or refer to the main documentation.