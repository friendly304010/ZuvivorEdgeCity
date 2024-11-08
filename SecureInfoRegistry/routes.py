from flask import render_template, request, jsonify, session, abort, redirect, url_for, send_from_directory
from app import app, db
from models import Report
from utils import encrypt_data, decrypt_data, check_overlap_between_reports, send_notification_to_victim
from analytics import get_report_trends
import json
from cryptography.fernet import InvalidToken
from functools import wraps
import os
from authlib.integrations.flask_client import OAuth

# Admin authentication (for demonstration purposes)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # In a real-world scenario, use a secure password and store it securely

oauth = OAuth()

def init_app(app):

    # Initialize OAuth
    
    oauth.init_app(app)
    oauth.register(
            name='worldcoin',
            client_id=os.environ.get('WORLDCOIN_CLIENT_ID'),
            client_secret=os.environ.get('WORLDCOIN_CLIENT_SECRET'),
            access_token_url='https://id.worldcoin.org/token',
            access_token_params=None,
            authorize_url='https://id.worldcoin.org/authorize',
            authorize_params=None,
            api_base_url='https://id.worldcoin.org/userinfo',
            client_kwargs={'scope': 'openid'},
        )

    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('admin_logged_in'):
                return abort(403)  # Forbidden
            return f(*args, **kwargs)
        return decorated_function

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/sw.js')
    def service_worker():
        return send_from_directory('static', 'sw.js')

    @app.route('/api/auth/signin')
    def worldcoin_login():
        redirect_uri = url_for('worldcoin_auth', _external=True)
        return oauth.worldcoin.authorize_redirect(redirect_uri)

    @app.route('/worldcoin/auth')
    def worldcoin_auth():
        token = oauth.worldcoin.authorize_access_token()
        user_info = oauth.worldcoin.parse_id_token(token)
        session['worldcoin_verified'] = True
        session['worldcoin_sub'] = user_info.get('sub')
        return redirect(url_for('index'))

    @app.route('/update_report', methods=['POST'])
    def update_report():
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        if 'current_report' not in session:
            session['current_report'] = {}
        
        field = list(data.keys())[0]
        value = data[field]
        
        if value.strip():
            session['current_report'][field] = value
        else:
            session['current_report'].pop(field, None)
        
        try:
            encrypted_data = encrypt_data(json.dumps(session['current_report']))
            temp_report = Report(encrypted_data=encrypted_data)
            overlap_count = check_overlap_between_reports(temp_report, Report.query.all())
            return jsonify({'success': True, 'overlap_count': overlap_count})
        except Exception as e:
            app.logger.error(f"Error updating report: {str(e)}")
            return jsonify({'success': False, 'message': 'An error occurred while updating the report'}), 500

    @app.route('/submit_report', methods=['POST'])
    def submit_report():
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        try:
            encrypted_data = encrypt_data(json.dumps(data))
            new_report = Report(
                encrypted_data=encrypted_data,
                perpetrator_name=data['perpetratorName'],
                perpetrator_description=data.get('perpetratorDescription', ''),
                perpetrator_email=data.get('perpetratorEmail', ''),
                perpetrator_phone=data.get('perpetratorPhone', ''),
                perpetrator_x_username=data.get('perpetratorXUsername', ''),
                perpetrator_telegram_username=data.get('perpetratorTelegramUsername', ''),
                incident_details=data['incidentDetails'],
                victim_email=data.get('victimEmail', '')
            )
            db.session.add(new_report)
            db.session.commit()

            overlap_count = check_overlap_between_reports(new_report, Report.query.all())
            new_report.overlap_count = overlap_count
            db.session.commit()

            if overlap_count > 0 and new_report.victim_email:
                send_notification_to_victim(new_report.victim_email, overlap_count)

            session.pop('current_report', None)
            return jsonify({'success': True, 'overlap_count': overlap_count})
        except InvalidToken:
            app.logger.error("Invalid encryption token")
            return jsonify({'success': False, 'message': 'An error occurred while encrypting the report'}), 500
        except Exception as e:
            app.logger.error(f"Error submitting report: {str(e)}")
            return jsonify({'success': False, 'message': 'An error occurred while submitting the report'}), 500

    @app.route('/get_reports', methods=['POST'])
    def get_reports():
        try:
            current_report_data = request.json
            if not current_report_data:
                return jsonify([])  # Return an empty list if no current report data

            encrypted_current_report = encrypt_data(json.dumps(current_report_data))
            current_report = Report(encrypted_data=encrypted_current_report)

            all_reports = Report.query.all()
            overlapping_reports = []

            for report in all_reports:
                if check_overlap_between_reports(current_report, [report]) > 0:
                    overlapping_reports.append({
                        'id': report.id,
                        'perpetrator_name': report.perpetrator_name,
                        'overlap_count': report.overlap_count,
                        'created_at': report.created_at.isoformat()
                    })

            return jsonify(overlapping_reports)
        except Exception as e:
            app.logger.error(f"Error fetching reports: {str(e)}")
            return jsonify([])  # Return an empty list in case of any error

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session['admin_logged_in'] = True
                return redirect(url_for('admin_dashboard'))
            else:
                return render_template('admin_login.html', error="Invalid credentials")
        return render_template('admin_login.html')

    @app.route('/admin/logout')
    def admin_logout():
        session.pop('admin_logged_in', None)
        return redirect(url_for('admin_login'))

    @app.route('/admin/dashboard')
    @admin_required
    def admin_dashboard():
        reports = Report.query.order_by(Report.created_at.desc()).all()
        return render_template('admin_dashboard.html', reports=reports)

    @app.route('/admin/analytics')
    @admin_required
    def admin_analytics():
        analytics = get_report_trends()
        return render_template('analytics_dashboard.html', analytics=analytics)

    @app.route('/admin/report/<int:report_id>')
    @admin_required
    def admin_view_report(report_id):
        report = Report.query.get_or_404(report_id)
        decrypted_data = json.loads(decrypt_data(report.encrypted_data))
        report_data = {
            'id': report.id,
            'perpetrator_name': report.perpetrator_name,
            'perpetrator_description': report.perpetrator_description,
            'perpetrator_email': report.perpetrator_email,
            'perpetrator_phone': report.perpetrator_phone,
            'perpetrator_x_username': report.perpetrator_x_username,
            'perpetrator_telegram_username': report.perpetrator_telegram_username,
            'incident_details': report.incident_details,
            'victim_email': report.victim_email,
            'overlap_count': report.overlap_count,
            'created_at': report.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        return jsonify(report_data)

    @app.route('/admin/report/<int:report_id>', methods=['DELETE'])
    @admin_required
    def admin_delete_report(report_id):
        report = Report.query.get_or_404(report_id)
        db.session.delete(report)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Report deleted successfully'})
