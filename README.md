# BizIT Analytics

## Secure Business Revenue & Profitability Analytics System

A full-stack web application for business analytics, featuring interactive dashboards, data uploads, and comprehensive reporting.

![Dashboard Preview](https://via.placeholder.com/800x400?text=BizIT+Analytics+Dashboard)

---

## 🚀 Features

### 1. Authentication & Security
- JWT-based authentication
- Role-based access control (Admin, Business Manager, Analyst)
- Password hashing with bcrypt
- Session management
- Protected dashboard routes

### 2. Interactive Dashboard
- Real-time KPI cards with animated counters
- Monthly revenue trend (Line Chart)
- Profit vs Cost comparison (Bar Chart)
- Department revenue distribution (Pie Chart)
- Profit margin trend analysis
- Sales volume tracking

### 3. Data Management
- CSV/Excel file upload support
- Data validation and error handling
- Duplicate record management
- Upload history tracking

### 4. Profitability Analysis
- Gross and net profit calculations
- Profit margin percentages
- Monthly growth rates
- Department-wise performance
- Top/worst performer identification

### 5. Alert System
- Automatic alerts for:
  - Revenue drops below threshold
  - Low profit margins (<10%)
  - Expenses exceeding revenue
- Real-time notification badges

### 6. Report Generation
- PDF business reports
- Excel data exports
- Monthly summary reports

---

## 🛠 Tech Stack

### Frontend
- HTML5 / CSS3
- JavaScript (ES6+)
- Chart.js for visualizations
- Font Awesome icons

### Backend
- Python 3.8+
- Flask (REST API)
- Flask-JWT-Extended
- Flask-SQLAlchemy
- Flask-CORS

### Database
- SQLite (Development)
- MySQL / PostgreSQL (Production)

---

## 📁 Project Structure

```
BizIT-Analytics/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── config.py           # Configuration settings
│   ├── models.py           # Database models
│   ├── auth.py             # Authentication routes
│   ├── api.py              # Business API routes
│   ├── utils.py            # Utility functions
│   └── requirements.txt    # Python dependencies
│
├── frontend/
│   ├── index.html          # Login page
│   ├── register.html       # Registration page
│   ├── dashboard.html      # Main dashboard
│   ├── upload.html         # File upload page
│   ├── reports.html        # Reports page
│   ├── css/
│   │   └── style.css       # Main stylesheet
│   └── js/
│       ├── auth.js         # Authentication utilities
│       ├── dashboard.js    # Dashboard functionality
│       ├── upload.js       # Upload functionality
│       └── reports.js      # Reports functionality
│
├── database/
│   └── schema.sql          # MySQL database schema
│
├── sample_data/
│   └── sample_business_data.csv
│
└── README.md
```

---

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- MySQL (optional, for production)

### Step 1: Clone or Download
```bash
cd BizIT-Analytics
```

### Step 2: Create Virtual Environment (Recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 4: Configure Database

#### For SQLite (Development - Default)
No additional configuration needed. The app will create `bizit_analytics.db` automatically.

#### For MySQL (Production)
1. Create a MySQL database:
```sql
CREATE DATABASE bizit_analytics;
```

2. Set environment variables:
```bash
# Windows
set MYSQL_HOST=localhost
set MYSQL_USER=root
set MYSQL_PASSWORD=your_password
set MYSQL_DB=bizit_analytics

# macOS/Linux
export MYSQL_HOST=localhost
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DB=bizit_analytics
```

3. Run the schema:
```bash
mysql -u root -p bizit_analytics < database/schema.sql
```

### Step 5: Run the Application
```bash
cd backend
python app.py
```

The application will start at:
- **Frontend:** http://localhost:5000
- **API:** http://localhost:5000/api

---

## 🔐 Default Login Credentials

| Email | Password | Role |
|-------|----------|------|
| admin@bizitanalytics.com | Admin@123 | Admin |

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/logout` | User logout |
| POST | `/api/auth/refresh` | Refresh access token |
| GET | `/api/auth/me` | Get current user |
| POST | `/api/auth/change-password` | Change password |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/kpis` | Get KPI summary |
| GET | `/api/dashboard/revenue-trend` | Get revenue trend data |
| GET | `/api/dashboard/department-distribution` | Get department breakdown |
| GET | `/api/dashboard/profit-margin-trend` | Get margin trend |
| GET | `/api/dashboard/sales-trend` | Get sales volume trend |

### Data Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/data` | Get paginated business data |
| POST | `/api/upload` | Upload CSV/Excel file |
| GET | `/api/upload/history` | Get upload history |
| GET | `/api/departments` | Get all departments |

### Analysis & Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analysis/profitability` | Get profitability analysis |
| GET | `/api/reports/pdf` | Download PDF report |
| GET | `/api/reports/excel` | Download Excel report |
| GET | `/api/reports/summary` | Get monthly summary |

### Alerts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/alerts` | Get all alerts |
| PUT | `/api/alerts/{id}/read` | Mark alert as read |
| PUT | `/api/alerts/read-all` | Mark all alerts read |

---

## 📊 CSV File Format

Your data file must include these columns:

| Column | Type | Required | Example |
|--------|------|----------|---------|
| Date | Date | Yes | 2024-01-15 |
| Revenue | Number | Yes | 150000.00 |
| Cost | Number | Yes | 85000.00 |
| Profit | Number | Yes | 65000.00 |
| Department | Text | Yes | Sales |
| Expenses | Number | Yes | 12000.00 |
| Sales Volume | Integer | Yes | 350 |

Sample file available at: `sample_data/sample_business_data.csv`

---

## 🔒 Security Features

- **Password Hashing:** Uses Werkzeug's secure password hashing
- **JWT Authentication:** Secure token-based authentication
- **Role-Based Access:** Admin, Business Manager, Analyst roles
- **SQL Injection Protection:** Uses SQLAlchemy ORM with parameterized queries
- **CORS Configuration:** Restricted to allowed origins
- **Token Refresh:** Automatic token refresh mechanism

---

## ⚡ Performance

- Handles 50,000+ records efficiently
- Pagination for large datasets
- Indexed database columns
- Efficient aggregation queries

---

## 🎨 UI Features

- Modern card-based dashboard layout
- Responsive design (mobile-friendly)
- Gradient header
- Animated KPI counters
- Smooth transitions
- Sidebar navigation
- Interactive charts with tooltips

---

## 🐛 Troubleshooting

### Common Issues

1. **Port 5000 in use:**
   ```bash
   # Change port in app.py
   app.run(port=8080)
   ```

2. **Module not found errors:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database connection error:**
   - Check MySQL is running
   - Verify credentials in environment variables

4. **PDF generation fails:**
   ```bash
   pip install reportlab
   ```

---

## 📝 License

This project is for educational purposes.

---

## 👤 Support

For issues or feature requests, please create an issue in the project repository.

---

**Built with ❤️ using Python Flask and JavaScript**
