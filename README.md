# mcp-personel-health

## Overview

This repository contains a **Firebase Cloud Function** that runs **twice daily** (11:30 AM and 11:30 PM Europe/Madrid time) and automatically processes health‑related CSV files stored in a Google Drive folder.

### What the function does

1. **Authenticates** to Google Drive using a service‑account with the `drive.readonly` scope.
2. **Searches** for CSV files whose name contains today’s date **or yesterday’s date** (format `YYYY.MM.DD`). This ensures the most recent complete file is always processed.
3. **Filters** results to only `.csv` files.
4. **Downloads** each CSV and parses it with `csv-parse`.
5. **Aggregates** health metrics:
   - **Weight** (`Peso` column) – first record.
   - **Average heart‑rate** (`Frecuencia cardiaca`).
   - **Total steps** (`Pasos`).
   - **Activities** (`RUNNING`, `WALKING`, `ACTIVIDADES`) – captured as an array of objects with type, distance, active time and timestamp.
6. **Writes** the aggregated data to Firestore under the collection `health_metrics` using the document ID `YYYY‑MM‑DD` (Madrid timezone) with a merge update.
7. **Logs** progress and any parsing errors; no HTTP response is sent because the function is scheduled, not HTTP‑triggered.

### Tech stack
- **Node.js 22 (2nd Gen)**
- **Firebase Functions v2** (`onSchedule`)
- **Google Drive API (v3)**
- **Firestore**
- **csv‑parse** for CSV parsing
- **TypeScript** (strict mode)

### Deployment
```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Deploy to Firebase (project must be set to mcp-personel-health)
firebase deploy --only functions --force
```

The function will be listed in the Cloud Scheduler console with the cron expression `30 11,23 * * *`.

---

*Feel free to customize the folder location, CSV layouts, or Firestore schema as needed.*
