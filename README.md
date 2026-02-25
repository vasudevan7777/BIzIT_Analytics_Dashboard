# BizIT Analytics Dashboard

A business analytics web app with interactive dashboards and data visualization.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Features

- 📊 Interactive Dashboard with Charts
- 📁 CSV/Excel File Upload
- 👥 Role-based Access (Admin, Manager, Analyst)
- 🔔 Alert Notifications
- 📈 Revenue & Profit Analysis
- 📄 PDF/Excel Reports

---

## Tech Stack

| Frontend | Backend | Database |
|----------|---------|----------|
| HTML/CSS/JS | Python Flask | SQLite |
| Chart.js | JWT Auth | SQLAlchemy |

---

## Quick Start

```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Run the app
python app.py

# 3. Open browser
http://localhost:5000
```

---

## Default Login

| Email | Password | Role |
|-------|----------|------|
| admin@bizitanalytics.com | Admin@123 | Admin |

---

## Project Structure

```
├── backend/
│   ├── app.py          # Main app
│   ├── api.py          # API routes
│   ├── auth.py         # Authentication
│   ├── models.py       # Database models
│   └── config.py       # Settings
│
├── frontend/
│   ├── index.html      # Login
│   ├── dashboard.html  # Dashboard
│   ├── upload.html     # Upload data
│   ├── admin.html      # Admin panel
│   └── css/js/         # Styles & Scripts
│
└── sample_data/        # Sample CSV files
```

---

## Screenshots

### Dashboard
- KPI Cards (Revenue, Cost, Profit)
- Revenue Trend Chart
- Department Distribution
- Profit Margin Analysis

### Features
- Upload CSV/Excel files
- Filter by date & department
- Download PDF/Excel reports
- Admin user management

---

## CSV Format

```csv
date,revenue,cost,profit,department,sales_volume
2026-01-15,50000,30000,20000,Sales,150
2026-01-16,45000,28000,17000,Marketing,120
```

---

## Deploy on Render

1. Push to GitHub
2. Connect repo on [render.com](https://render.com)
3. Deploy as Web Service

---

## Author

**Sri Bharath**

---

## License

MIT License
