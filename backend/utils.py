"""
BizIT Analytics - Utility Functions
"""
import os
import pandas as pd
from datetime import datetime
from werkzeug.utils import secure_filename
from models import db, BusinessData, Alert, UploadHistory
from config import Config
import io

# Ensure upload folder exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def validate_columns(df):
    """Validate that required columns exist in DataFrame"""
    required_columns = ['Date', 'Revenue', 'Cost', 'Profit', 'Department', 'Expenses', 'Sales Volume']
    
    # Normalize column names (case-insensitive)
    df.columns = [col.strip().title() for col in df.columns]
    
    # Handle common variations
    column_mapping = {
        'Sales_Volume': 'Sales Volume',
        'Salesvolume': 'Sales Volume',
        'Sales': 'Sales Volume'
    }
    df.rename(columns=column_mapping, inplace=True)
    
    missing_columns = []
    for col in required_columns:
        if col not in df.columns:
            missing_columns.append(col)
    
    return missing_columns, df


def process_upload_file(file, user_id):
    """Process uploaded CSV/Excel file"""
    if not file or not allowed_file(file.filename):
        return {
            'status': 'error',
            'message': 'Invalid file format. Please upload CSV or Excel file.'
        }
    
    filename = secure_filename(file.filename)
    
    try:
        # Read file into DataFrame
        if filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        
        # Validate columns
        missing_cols, df = validate_columns(df)
        if missing_cols:
            return {
                'status': 'error',
                'message': f'Missing required columns: {", ".join(missing_cols)}'
            }
        
        # Process data
        records_added = 0
        records_updated = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                # Parse date
                date_value = row['Date']
                if isinstance(date_value, str):
                    date_obj = pd.to_datetime(date_value).date()
                else:
                    date_obj = pd.to_datetime(date_value).date()
                
                # Check for existing record (same date and department)
                existing = BusinessData.query.filter_by(
                    date=date_obj,
                    department=str(row['Department']).strip()
                ).first()
                
                if existing:
                    # Update existing record
                    existing.revenue = float(row['Revenue'])
                    existing.cost = float(row['Cost'])
                    existing.profit = float(row['Profit'])
                    existing.expenses = float(row.get('Expenses', 0))
                    existing.sales_volume = int(row.get('Sales Volume', 0))
                    records_updated += 1
                else:
                    # Create new record
                    new_data = BusinessData(
                        date=date_obj,
                        revenue=float(row['Revenue']),
                        cost=float(row['Cost']),
                        profit=float(row['Profit']),
                        department=str(row['Department']).strip(),
                        expenses=float(row.get('Expenses', 0)),
                        sales_volume=int(row.get('Sales Volume', 0)),
                        created_by=user_id
                    )
                    db.session.add(new_data)
                    records_added += 1
                
            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
        
        db.session.commit()
        
        # Generate alerts for new/updated data
        all_data = BusinessData.query.all()
        generate_alerts(all_data)
        
        # Log upload history
        upload_log = UploadHistory(
            filename=filename,
            records_count=records_added + records_updated,
            status='success' if not errors else 'partial',
            error_message='\n'.join(errors[:10]) if errors else None,
            uploaded_by=user_id
        )
        db.session.add(upload_log)
        db.session.commit()
        
        return {
            'status': 'success',
            'message': f'Successfully processed {records_added + records_updated} records',
            'records_added': records_added,
            'records_updated': records_updated,
            'errors': errors[:10] if errors else []
        }
        
    except Exception as e:
        # Log failed upload
        upload_log = UploadHistory(
            filename=filename,
            records_count=0,
            status='failed',
            error_message=str(e),
            uploaded_by=user_id
        )
        db.session.add(upload_log)
        db.session.commit()
        
        return {
            'status': 'error',
            'message': f'Failed to process file: {str(e)}'
        }


def calculate_kpis(data):
    """Calculate KPIs from business data"""
    if not data:
        return {
            'total_revenue': 0,
            'total_cost': 0,
            'total_expenses': 0,
            'net_profit': 0,
            'profit_margin': 0,
            'total_sales_volume': 0,
            'monthly_growth': 0,
            'record_count': 0
        }
    
    total_revenue = sum(d.revenue for d in data)
    total_cost = sum(d.cost for d in data)
    total_expenses = sum(d.expenses for d in data)
    net_profit = sum(d.profit for d in data)
    total_sales = sum(d.sales_volume for d in data)
    
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Calculate monthly growth (compare last two months)
    monthly_growth = calculate_monthly_growth(data)
    
    return {
        'total_revenue': round(total_revenue, 2),
        'total_cost': round(total_cost, 2),
        'total_expenses': round(total_expenses, 2),
        'net_profit': round(net_profit, 2),
        'profit_margin': round(profit_margin, 2),
        'total_sales_volume': total_sales,
        'monthly_growth': round(monthly_growth, 2),
        'record_count': len(data)
    }


def calculate_monthly_growth(data):
    """Calculate month-over-month growth rate"""
    if not data:
        return 0
    
    # Group by month
    monthly_revenue = {}
    for d in data:
        month_key = d.date.strftime('%Y-%m')
        if month_key not in monthly_revenue:
            monthly_revenue[month_key] = 0
        monthly_revenue[month_key] += d.revenue
    
    if len(monthly_revenue) < 2:
        return 0
    
    # Sort months and get last two
    sorted_months = sorted(monthly_revenue.keys())
    current_month = monthly_revenue[sorted_months[-1]]
    previous_month = monthly_revenue[sorted_months[-2]]
    
    if previous_month > 0:
        growth = ((current_month - previous_month) / previous_month) * 100
        return growth
    return 0


def generate_alerts(data):
    """Generate business alerts based on data analysis"""
    if not data:
        return
    
    # Group data by department for analysis
    dept_data = {}
    for d in data:
        if d.department not in dept_data:
            dept_data[d.department] = []
        dept_data[d.department].append(d)
    
    for dept, records in dept_data.items():
        total_revenue = sum(r.revenue for r in records)
        total_profit = sum(r.profit for r in records)
        total_expenses = sum(r.expenses for r in records)
        
        # Calculate profit margin
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Check for low profit margin
        if profit_margin < Config.PROFIT_MARGIN_THRESHOLD:
            existing_alert = Alert.query.filter_by(
                type='low_margin',
                department=dept,
                is_read=False
            ).first()
            
            if not existing_alert:
                alert = Alert(
                    type='low_margin',
                    message=f'Low profit margin ({profit_margin:.1f}%) detected in {dept}',
                    severity='warning',
                    department=dept
                )
                db.session.add(alert)
        
        # Check if expenses exceed revenue
        if total_expenses > total_revenue:
            existing_alert = Alert.query.filter_by(
                type='expense_exceed',
                department=dept,
                is_read=False
            ).first()
            
            if not existing_alert:
                alert = Alert(
                    type='expense_exceed',
                    message=f'Expenses exceed revenue in {dept}!',
                    severity='danger',
                    department=dept
                )
                db.session.add(alert)
    
    # Check for revenue drop (compare months)
    monthly_data = {}
    for d in data:
        month_key = d.date.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = 0
        monthly_data[month_key] += d.revenue
    
    if len(monthly_data) >= 2:
        sorted_months = sorted(monthly_data.keys())
        current = monthly_data[sorted_months[-1]]
        previous = monthly_data[sorted_months[-2]]
        
        if previous > 0:
            drop = ((previous - current) / previous) * 100
            if drop > Config.REVENUE_DROP_THRESHOLD:
                existing_alert = Alert.query.filter_by(
                    type='revenue_drop',
                    is_read=False
                ).first()
                
                if not existing_alert:
                    alert = Alert(
                        type='revenue_drop',
                        message=f'Revenue dropped by {drop:.1f}% compared to last month',
                        severity='danger',
                        department=None
                    )
                    db.session.add(alert)
    
    db.session.commit()


def generate_pdf_report(start_date=None, end_date=None, department=None):
    """Generate PDF business report"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        
        # Query data
        query = BusinessData.query
        if start_date:
            query = query.filter(BusinessData.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(BusinessData.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        if department and department != 'all':
            query = query.filter(BusinessData.department == department)
        
        data = query.order_by(BusinessData.date.desc()).all()
        kpis = calculate_kpis(data)
        
        # Create PDF
        filename = f'business_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1
        )
        elements.append(Paragraph("BizIT Analytics - Business Report", title_style))
        elements.append(Spacer(1, 20))
        
        # Report info
        info_style = styles['Normal']
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", info_style))
        if start_date and end_date:
            elements.append(Paragraph(f"Period: {start_date} to {end_date}", info_style))
        if department and department != 'all':
            elements.append(Paragraph(f"Department: {department}", info_style))
        elements.append(Spacer(1, 20))
        
        # KPI Summary
        elements.append(Paragraph("Key Performance Indicators", styles['Heading2']))
        kpi_data = [
            ['Metric', 'Value'],
            ['Total Revenue', f"${kpis['total_revenue']:,.2f}"],
            ['Total Cost', f"${kpis['total_cost']:,.2f}"],
            ['Net Profit', f"${kpis['net_profit']:,.2f}"],
            ['Profit Margin', f"{kpis['profit_margin']:.2f}%"],
            ['Monthly Growth', f"{kpis['monthly_growth']:.2f}%"],
            ['Total Sales Volume', f"{kpis['total_sales_volume']:,}"]
        ]
        
        kpi_table = Table(kpi_data, colWidths=[3*inch, 2*inch])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90A4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD'))
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 30))
        
        # Data Table (limited rows for readability)
        elements.append(Paragraph("Business Data Summary", styles['Heading2']))
        table_data = [['Date', 'Department', 'Revenue', 'Cost', 'Profit', 'Sales']]
        
        for record in data[:50]:  # Limit to 50 records
            table_data.append([
                record.date.strftime('%Y-%m-%d'),
                record.department[:15],
                f"${record.revenue:,.2f}",
                f"${record.cost:,.2f}",
                f"${record.profit:,.2f}",
                f"{record.sales_volume:,}"
            ])
        
        data_table = Table(table_data, colWidths=[1.2*inch, 1.2*inch, 1*inch, 1*inch, 1*inch, 0.8*inch])
        data_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90A4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')])
        ]))
        elements.append(data_table)
        
        doc.build(elements)
        return filepath
        
    except ImportError:
        # If reportlab is not installed, return None
        print("ReportLab not installed. PDF generation unavailable.")
        return None
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None


def generate_excel_report(start_date=None, end_date=None, department=None):
    """Generate Excel business report"""
    try:
        # Query data
        query = BusinessData.query
        if start_date:
            query = query.filter(BusinessData.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(BusinessData.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        if department and department != 'all':
            query = query.filter(BusinessData.department == department)
        
        data = query.order_by(BusinessData.date.desc()).all()
        kpis = calculate_kpis(data)
        
        # Create Excel file
        filename = f'business_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # KPI Summary Sheet
            kpi_df = pd.DataFrame({
                'Metric': ['Total Revenue', 'Total Cost', 'Total Expenses', 'Net Profit', 
                          'Profit Margin (%)', 'Monthly Growth (%)', 'Total Sales Volume'],
                'Value': [kpis['total_revenue'], kpis['total_cost'], kpis['total_expenses'],
                         kpis['net_profit'], kpis['profit_margin'], kpis['monthly_growth'],
                         kpis['total_sales_volume']]
            })
            kpi_df.to_excel(writer, sheet_name='KPI Summary', index=False)
            
            # Raw Data Sheet
            data_records = [{
                'Date': d.date.strftime('%Y-%m-%d'),
                'Department': d.department,
                'Revenue': d.revenue,
                'Cost': d.cost,
                'Expenses': d.expenses,
                'Profit': d.profit,
                'Sales Volume': d.sales_volume,
                'Profit Margin (%)': round((d.profit / d.revenue * 100) if d.revenue > 0 else 0, 2)
            } for d in data]
            
            data_df = pd.DataFrame(data_records)
            data_df.to_excel(writer, sheet_name='Business Data', index=False)
            
            # Department Summary Sheet
            dept_summary = data_df.groupby('Department').agg({
                'Revenue': 'sum',
                'Cost': 'sum',
                'Profit': 'sum',
                'Sales Volume': 'sum'
            }).reset_index()
            dept_summary['Profit Margin (%)'] = round(
                dept_summary['Profit'] / dept_summary['Revenue'] * 100, 2
            )
            dept_summary.to_excel(writer, sheet_name='Department Summary', index=False)
        
        return filepath
        
    except Exception as e:
        print(f"Error generating Excel: {e}")
        return None
