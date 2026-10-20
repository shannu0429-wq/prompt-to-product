from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.content import ProblemStatement, Announcement, FAQ
from app.models.evaluation import Result
from app.services.settings_service import SettingsService

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    status_text, status_class = SettingsService.get_event_status()
    problem_statement = ProblemStatement.get_published()
    announcements = Announcement.query.filter_by(is_published=True).order_by(Announcement.published_at.desc()).limit(5).all()
    faqs = FAQ.query.filter_by(is_published=True).order_by(FAQ.display_order.asc(), FAQ.id.asc()).all()
    results = None
    results_published = SettingsService.get_setting('results_published', 'false').lower() == 'true'
    if results_published:
        results = Result.query.filter_by(is_published=True).order_by(Result.rank.asc()).all()

    return render_template(
        'index.html',
        event_status_text=status_text,
        event_status_class=status_class,
        problem_statement=problem_statement,
        announcements=announcements,
        faqs=faqs,
        results_published=results_published,
        results=results,
    )


@public_bp.route('/about')
def about():
    status_text, status_class = SettingsService.get_event_status()
    return render_template(
        'about.html',
        event_status_text=status_text,
        event_status_class=status_class,
    )


@public_bp.route('/problem-statement')
def problem_statement():
    problem = ProblemStatement.get_published()
    return render_template(
        'problem_statement.html',
        problem=problem,
    )


@public_bp.route('/rules')
def rules():
    return render_template('rules.html')


@public_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        if not name or not email or not message:
            flash('Please fill out all required fields.', 'danger')
        else:
            flash('Thank you for contacting the organizing team! We will get back to you shortly.', 'success')
            return redirect(url_for('public.contact'))
    return render_template('contact.html')
