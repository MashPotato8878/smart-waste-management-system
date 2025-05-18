from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from ..models import Bin, OverflowReport, CollectionSchedule, RecyclingTip, User
from .. import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    user_reports = OverflowReport.query.filter_by(user_id=current_user.id).order_by(OverflowReport.report_date.desc()).limit(5).all()
    nearby_bins = Bin.query.filter_by(location=current_user.address).all()
    upcoming_collections = CollectionSchedule.query.filter(
        CollectionSchedule.collection_time > datetime.utcnow()
    ).order_by(CollectionSchedule.collection_time).limit(5).all()
    
    return render_template('main/dashboard.html',
                         user_reports=user_reports,
                         nearby_bins=nearby_bins,
                         upcoming_collections=upcoming_collections)

@main_bp.route('/bin-status')
@login_required
def bin_status():
    bins = Bin.query.all()
    return render_template('main/bin_status.html', bins=bins)

@main_bp.route('/collection-schedule')
@login_required
def collection_schedule():
    address = request.args.get('address', current_user.address)
    schedule = CollectionSchedule.query.join(Bin).filter(Bin.location == address).all()
    return render_template('main/collection_schedule.html', schedule=schedule)

@main_bp.route('/report-overflow', methods=['GET', 'POST'])
@login_required
def report_overflow():
    if request.method == 'POST':
        bin_id = request.form.get('bin_id')
        photo = request.files.get('photo')
        notes = request.form.get('notes')
        
        if not bin_id:
            flash('Please select a bin')
            return redirect(url_for('main.report_overflow'))
            
        if photo:
            filename = secure_filename(f"overflow_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{photo.filename}")
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)  # Ensure directory exists
            photo_path = os.path.join('uploads', filename)
            photo.save(os.path.join(upload_folder, filename))
        else:
            photo_path = None
            
        report = OverflowReport(
            bin_id=bin_id,
            user_id=current_user.id,
            photo_path=photo_path,
            notes=notes
        )
        
        try:
            db.session.add(report)
            # Update bin status
            bin = Bin.query.get(bin_id)
            bin.update_status('full')
            db.session.commit()
            flash('Report submitted successfully')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.')
            
    bins = Bin.query.all()
    return render_template('main/report_overflow.html', bins=bins)

@main_bp.route('/recycling-tips')
def recycling_tips():
    tips = {
        'plastic': RecyclingTip.query.filter_by(category='plastic').all(),
        'organic': RecyclingTip.query.filter_by(category='organic').all(),
        'electronics': RecyclingTip.query.filter_by(category='electronics').all()
    }
    return render_template('main/recycling_tips.html', tips=tips)

@main_bp.route('/set-notification-preferences', methods=['POST'])
@login_required
def set_notification_preferences():
    email_notification = request.form.get('emailNotification') == 'on'
    reminder_notification = request.form.get('reminderNotification') == 'on'
    
    try:
        current_user.email_notifications = email_notification
        current_user.reminder_notifications = reminder_notification
        db.session.commit()
        flash('Notification preferences updated successfully')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.')
        
    return redirect(url_for('main.collection_schedule'))

@main_bp.route('/add-bin', methods=['GET', 'POST'])
@login_required
def add_bin():
    if not current_user.is_admin:
        flash('Only administrators can add new bins.', 'danger')
        return redirect(url_for('main.bin_status'))

    if request.method == 'POST':
        location = request.form.get('location')
        status = request.form.get('status')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        # Validate required fields
        if not all([location, status, latitude, longitude]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('main.add_bin'))

        try:
            # Convert coordinates to float
            latitude = float(latitude)
            longitude = float(longitude)

            # Validate coordinate ranges
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                flash('Invalid coordinates.', 'danger')
                return redirect(url_for('main.add_bin'))

            # Create new bin
            new_bin = Bin(
                location=location,
                latitude=latitude,
                longitude=longitude,
                status=status,
                last_updated=datetime.utcnow()
            )

            db.session.add(new_bin)
            db.session.commit()

            flash('Bin added successfully!', 'success')
            return redirect(url_for('main.bin_status'))

        except ValueError:
            flash('Invalid coordinate values.', 'danger')
            return redirect(url_for('main.add_bin'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding bin: {str(e)}', 'danger')
            return redirect(url_for('main.add_bin'))

    return render_template('main/add_bin.html')

@main_bp.route('/admin/reports')
@login_required
def admin_reports():
    if not current_user.is_admin:
        flash('Admins only.', 'danger')
        return redirect(url_for('main.dashboard'))
    status_filter = request.args.get('status')
    if status_filter:
        reports = OverflowReport.query.filter_by(status=status_filter).order_by(OverflowReport.report_date.desc()).all()
    else:
        reports = OverflowReport.query.order_by(OverflowReport.report_date.desc()).all()
    return render_template('admin/reports.html', reports=reports)

@main_bp.route('/admin/reports/<int:report_id>/status', methods=['POST'])
@login_required
def update_report_status(report_id):
    if not current_user.is_admin:
        flash('Admins only.', 'danger')
        return redirect(url_for('main.dashboard'))
    new_status = request.form.get('status')
    report = OverflowReport.query.get_or_404(report_id)
    if new_status in ['pending', 'resolved']:
        report.status = new_status
        db.session.commit()
        flash('Report status updated.', 'success')
    else:
        flash('Invalid status.', 'danger')
    return redirect(url_for('main.admin_reports'))

@main_bp.route('/make-me-admin')
@login_required
def make_me_admin():
    from ..models import User
    user = User.query.filter_by(username=current_user.username).first()
    user.is_admin = True
    db.session.commit()
    return "You are now an admin!" 