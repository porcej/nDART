from flask import redirect, url_for, request, flash, send_file, abort
from flask_login import login_required, current_user
from extensions import db
from models import User, Role, ChatRoom, ChatMessage, StationStatus, Assignment, ObservationsCategory, Agency
from datetime import datetime, UTC
from uuid import uuid4
from functools import wraps
import pandas as pd
from io import BytesIO

# Admin access decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login', next=request.url))
            
        if not current_user.has_role('admin'):
            flash('You need admin privileges to access this page.', 'error')
            return redirect(url_for('main_bp.dashboard'))
            
        return f(*args, **kwargs)
    return decorated_function

# Load XLSX file to Dict
def load_xlsx(file):
    df = pd.read_excel(file)
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    return df


def clean_str(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return s if s else None


def clean_int(val, default=0):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return default
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return default


def clean_bool(val, default=True):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return default
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return bool(int(val))
    s = str(val).strip().lower()
    if s in ('true', '1', 'yes', 'y'):
        return True
    if s in ('false', '0', 'no', 'n'):
        return False
    return default

# Save Dict to XLSX file
def save_xlsx(df, file):
    df.to_excel(file, index=False)

# -----------------
# Import/Export
# -----------------
def save_to_database(df, table, password=None):
    # Get the appropriate model class based on the table name
    model_map = {
        'agency': Agency,
        'station_status': StationStatus,
        'assignments': Assignment,
        'observations_categories': ObservationsCategory,
        'chat_messages': ChatMessage,
        'users': User,
        'roles': Role,
        'chat_rooms': ChatRoom
    }
    
    model_class = model_map.get(table)
    if not model_class:
        abort(404, description=f"Table {table} not found")

    # Normalize column names (lowercase and replace spaces with underscores)
    df.columns = df.columns.str.lower().str.replace(' ', '_')

    # Get valid model fields
    model_fields = [column.key for column in model_class.__table__.columns]
    
    # Filter DataFrame to only include valid model fields
    valid_columns = [col for col in df.columns if col in model_fields]
    df = df[valid_columns]

    # Delete existing records
    model_class.query.delete()
    
    # Get the model's datetime columns
    datetime_columns = []
    for column in model_class.__table__.columns:
        if isinstance(column.type, db.DateTime):
            datetime_columns.append(column.name)
    
    # Convert DataFrame records to model instances
    for _, row in df.iterrows():
        # Convert row to dict and handle NaN/None values
        data = row.to_dict()
        for key, value in data.items():
            print(f'Key: {key}, Value: {value}, current user: {current_user.name}')
            # Handle NaN/None values
            if pd.isna(value):
                data[key] = None
                continue

            if key == 'date_of_birth':
                pass
            # Convert datetime strings to datetime objects
            elif key in datetime_columns and value is not None:
                try:
                    if isinstance(value, str):
                        # Try parsing various datetime formats
                        try:
                            data[key] = datetime.fromisoformat(value)
                        except ValueError:
                            try:
                                data[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                data[key] = pd.to_datetime(value).to_pydatetime()
                    elif isinstance(value, pd.Timestamp):
                        data[key] = value.to_pydatetime()
                    # Ensure timezone awareness
                    if data[key] and data[key].tzinfo is None:
                        data[key] = data[key].replace(tzinfo=UTC)
                except Exception as e:
                    print(f"Error converting datetime for {key}: {value} - {str(e)}")
                    data[key] = None
        
        try:
            # Create new instance and add to session
            instance = model_class(**data)
            if table == 'users' and password:
                instance.set_password(password)
            db.session.add(instance)
        except Exception as e:
            print(f"Error creating instance: {str(e)}")
            print(f"Data: {data}")
            db.session.rollback()
            raise
    
    # Commit all changes
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise

def _max_excel_column_width(series, header_len):
    """Widest cell as character count; avoids apply(len) on raw NaN/float (pandas TypeError)."""
    if series.empty:
        return header_len + 1
    content_max = series.map(lambda v: len(str(v))).max()
    if pd.isna(content_max):
        content_max = 0
    return max(int(content_max), header_len) + 1

def export_to_xlsx(table):
    # Get the appropriate model class based on the table name
    model_map = {
        'agency': Agency,
        'agencies': Agency,
        'station_status': StationStatus,
        'assignments': Assignment,
        'observations_categories': ObservationsCategory,
        'chat_messages': ChatMessage,
        'users': User,
        'roles': Role,
        'chat_rooms': ChatRoom
    }
    
    model_class = model_map.get(table)
    if not model_class:
        abort(404, description=f"Table {table} not found")
    
    # Query all records and convert to dictionaries
    records = [record.to_dict() for record in model_class.query.all()]
    
    # Convert to DataFrame (omit primary key so imports always get new ids)
    df = pd.DataFrame(records)
    if 'id' in df.columns:
        df = df.drop(columns=['id'])
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=table)
        
        # Auto-adjust columns' width
        worksheet = writer.sheets[table]
        for idx, col in enumerate(df.columns):
            series = df[col]
            max_len = _max_excel_column_width(series, len(str(col)))
            worksheet.set_column(idx, idx, max_len)  # set column width
    
    output.seek(0)
    return send_file(
        output,
        download_name=f'{table}.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )