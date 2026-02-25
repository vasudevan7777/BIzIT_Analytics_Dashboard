"""
BizIT Analytics - Database Models
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
import csv

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication and role management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='Analyst')  # Admin, Business Manager, Analyst
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationship to business data
    business_data = db.relationship('BusinessData', backref='creator', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.email}>'


class BusinessData(db.Model):
    """Business data model for storing uploaded financial data"""
    __tablename__ = 'business_data'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    revenue = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    expenses = db.Column(db.Float, nullable=False, default=0)
    profit = db.Column(db.Float, nullable=False)
    department = db.Column(db.String(100), nullable=False, index=True)
    sales_volume = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Unique constraint to prevent duplicate records
    __table_args__ = (
        db.UniqueConstraint('date', 'department', name='unique_date_department'),
    )
    
    def to_dict(self):
        """Convert business data to dictionary"""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'revenue': self.revenue,
            'cost': self.cost,
            'expenses': self.expenses,
            'profit': self.profit,
            'department': self.department,
            'sales_volume': self.sales_volume,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if self.revenue > 0:
            return round((self.profit / self.revenue) * 100, 2)
        return 0
    
    def __repr__(self):
        return f'<BusinessData {self.date} - {self.department}>'


class Alert(db.Model):
    """Alert model for business notifications"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # revenue_drop, low_margin, expense_exceed
    message = db.Column(db.String(500), nullable=False)
    severity = db.Column(db.String(20), nullable=False, default='warning')  # info, warning, danger
    department = db.Column(db.String(100))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert alert to dictionary"""
        return {
            'id': self.id,
            'type': self.type,
            'message': self.message,
            'severity': self.severity,
            'department': self.department,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Alert {self.type} - {self.severity}>'


class UploadHistory(db.Model):
    """Track file upload history"""
    __tablename__ = 'upload_history'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    records_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='success')  # success, failed, partial
    error_message = db.Column(db.Text)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='uploads')
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'records_count': self.records_count,
            'status': self.status,
            'error_message': self.error_message,
            'uploaded_by': self.uploaded_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


def init_db(app):
    """Initialize database and create tables"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        # Create default admin user if not exists
        if not User.query.filter_by(email='admin@bizitanalytics.com').first():
            admin = User(
                name='Administrator',
                email='admin@bizitanalytics.com',
                role='Admin'
            )
            admin.set_password('Admin@123')
            db.session.add(admin)
            db.session.commit()
            print('Default admin user created: admin@bizitanalytics.com / Admin@123')
        
        # Load sample data if database is empty
        if BusinessData.query.count() == 0:
            load_sample_data(app)


def load_sample_data(app):
    """Load sample data from CSV files"""
    sample_dir = os.path.join(os.path.dirname(__file__), '..', 'sample_data')
    
    csv_files = [
        'business_dataset_150_records.csv',
        'sample_business_data.csv'
    ]
    
    total_loaded = 0
    
    for csv_file in csv_files:
        file_path = os.path.join(sample_dir, csv_file)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Normalize column names (handle variations)
                        date_str = row.get('Date', row.get('date', ''))
                        revenue = float(row.get('Revenue', row.get('revenue', 0)))
                        cost = float(row.get('Cost', row.get('cost', 0)))
                        expenses = float(row.get('Expenses', row.get('expenses', 0)))
                        profit = float(row.get('Profit', row.get('profit', 0)))
                        department = row.get('Department', row.get('department', 'Unknown'))
                        sales_vol = row.get('Sales_Volume', row.get('Sales Volume', row.get('sales_volume', 0)))
                        sales_volume = int(sales_vol) if sales_vol else 0
                        
                        # Parse date
                        try:
                            date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        except:
                            continue
                        
                        # Check if record already exists
                        existing = BusinessData.query.filter_by(
                            date=date, 
                            department=department
                        ).first()
                        
                        if not existing:
                            business_data = BusinessData(
                                date=date,
                                revenue=revenue,
                                cost=cost,
                                expenses=expenses,
                                profit=profit,
                                department=department,
                                sales_volume=sales_volume
                            )
                            db.session.add(business_data)
                            total_loaded += 1
                    
                    db.session.commit()
                    print(f'Loaded data from {csv_file}')
            except Exception as e:
                print(f'Error loading {csv_file}: {e}')
                db.session.rollback()
    
    print(f'Total sample records loaded: {total_loaded}')
    
    # Create sample alerts
    if Alert.query.count() == 0:
        sample_alerts = [
            Alert(
                type='revenue_milestone',
                message='Congratulations! Monthly revenue exceeded $1M target',
                severity='info',
                department='Sales'
            ),
            Alert(
                type='profit_alert',
                message='HR department showing negative profit margin - review expenses',
                severity='warning',
                department='HR'
            ),
            Alert(
                type='growth_alert',
                message='Operations department achieved 15% growth this quarter',
                severity='info',
                department='Operations'
            )
        ]
        for alert in sample_alerts:
            db.session.add(alert)
        db.session.commit()
        print('Sample alerts created')
