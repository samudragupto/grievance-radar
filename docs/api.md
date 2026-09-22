# Grievance Radar REST API Documentation

Base URL: `/api`

### 1. Ingest Complaints
- **Endpoint**: `POST /api/upload`
- **Content-Type**: `multipart/form-data`
- **Body**: `file` (`.csv` or `.json` file of citizen complaints)
- **Response**:
  ```json
  {
    "imported": 1200,
    "skipped": 0
  }
  ```

### 2. Trigger Pipeline Execution
- **Endpoint**: `POST /api/pipeline`
- **Description**: Triggers embedding generation, clustering, rolling baseline computation, and anomaly spike detection.
- **Response**:
  ```json
  {
    "success": true,
    "clusters_found": 14,
    "spikes_detected": 3,
    "top_findings": [
      {
        "id": 1,
        "title": "Water Supply surge in Ward 4 (+340%, z=4.2)",
        "z_score": 4.2,
        "percent_change": 340.0,
        "affected_count": 65,
        "wards": ["Ward 4"],
        "suggested_dept": "Water Supply",
        "status": "pending"
      }
    ]
  }
  ```

### 3. List Discovered Clusters
- **Endpoint**: `GET /api/clusters`
- **Response**:
  ```json
  [
    {
      "id": 0,
      "label": "Water Supply | Leakage | Pipe | Overhead",
      "count": 145,
      "avg_zscore": 0.35,
      "max_zscore": 4.2
    }
  ]
  ```

### 4. Query Anomaly Findings
- **Endpoint**: `GET /api/findings?status={pending|confirmed|dismissed}`
- **Response**: Array of Finding objects matching status.

### 5. Officer Decision (Human-in-the-loop)
- **Endpoint**: `POST /officer/decision`
- **Content-Type**: `application/json`
- **Body**:
  ```json
  {
    "finding_id": 1,
    "action": "confirm",
    "edited_title": "Critical Water Line Rupture in Ward 4",
    "edited_dept": "Water Supply & Sewerage"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "message": "Finding #1 successfully confirmed."
  }
  ```

### 6. Generate Monday Brief PDF
- **Endpoint**: `POST /api/brief`
- **Response**:
  ```json
  {
    "success": true,
    "brief_id": 1,
    "week_label": "Week 38, 2026",
    "download_url": "/brief/download/1"
  }
  ```

### 7. Public Trends & Geospatial Data
- **Endpoint**: `GET /api/trends`
- **Description**: Returns aggregated time series and ward coordinates. Zero citizen PII or individual complaint texts are returned.
- **Response**:
  ```json
  {
    "weeks": ["2026-W05", "2026-W06", "2026-W07", "2026-W08"],
    "categories": {
      "Water Supply": [12, 14, 15, 65],
      "Sanitation": [18, 19, 18, 38]
    },
    "ward_counts": [{"ward": "Ward 4", "count": 142}],
    "ward_geo": [{"ward": "Ward 4", "count": 142, "lat": 10.835, "lng": 78.705}]
  }
  ```
