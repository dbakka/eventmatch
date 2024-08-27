import sys
print(sys.executable)
print(sys.path)

from flask import Flask, render_template, request, redirect, url_for, session, flash
from event_classes import Event, Attendee, MatchMaker
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim
import time
import random
import qrcode
import io
import base64
import os
import string
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from flask_mail import Mail, Message

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

import os

template_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(template_dir, 'templates')
app = Flask(__name__, template_folder=template_dir)
print("Template folder path:", app.template_folder)
print("Templates in folder:", os.listdir(app.template_folder))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback_secret_key')
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)

# Predefined list of event themes
EVENT_THEMES = [
    "Technology", "Business", "Arts", "Science", "Sports", "Music", "Food", 
    "Travel", "Health", "Education", "Environment", "Fashion", "Gaming", 
    "Literature", "Politics", "Film", "Photography", "Dance", "Networking", "Charity"
]

# Dictionary to store events by their unique codes
events = {}

@app.route('/suggest_theme', methods=['POST'])
def suggest_theme():
    event_name = request.json['event_name'].lower()
    suggested_themes = [theme for theme in EVENT_THEMES if any(word in event_name for word in theme.lower().split())]
    return jsonify(suggested_themes[:5])  # Return top 5 suggestions

def geocode_with_retry(address, attempt=1, max_attempts=5):
    try:
        geolocator = Nominatim(user_agent="your_app_name")
        result = geolocator.geocode(address)
        time.sleep(1)  # Add a 1-second delay between requests
        return result
    except GeocoderTimedOut:
        if attempt <= max_attempts:
            return geocode_with_retry(address, attempt=attempt+1)
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        app.logger.debug('Received POST request to create_event')
        try:
            app.logger.debug('Form data: %s', request.form)
            name = request.form['name']
            creator = request.form['creator']
            creator_email = request.form['creator_email']
            location = request.form['location']
            radius = float(request.form['radius'])
            
            app.logger.debug('Creating new event with: name=%s, creator=%s, creator_email=%s, location=%s, radius=%s', 
                             name, creator, creator_email, location, radius)
            new_event = Event(name, location, creator, creator_email, radius)
            app.logger.debug('New event created: %s', new_event.__dict__)
            events[new_event.code] = new_event

            app.logger.debug('Storing event code in session')
            session['event_code'] = new_event.code

            app.logger.debug('Generating QR code')
            qr_code_url = generate_qr_code(new_event.code)

            app.logger.debug('Sending confirmation email')
            send_confirmation_email(new_event, url_for('register_attendee', share_id=new_event.share_id, _external=True), qr_code_url)

            app.logger.debug('Event creation successful')
            flash('Event created successfully! Check your email for details.', 'success')
            return redirect(url_for('dashboard', event_code=new_event.code))
        except Exception as e:
            app.logger.error('Error creating event: %s', str(e), exc_info=True)
            flash('An error occurred while creating the event. Please try again.', 'error')
            return redirect(url_for('create_event'))

    return render_template('create_event.html', EVENT_THEMES=EVENT_THEMES)

@app.route('/dashboard/<event_code>')
def dashboard(event_code):
    event = events.get(event_code)
    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('index'))
    
    is_creator = session.get('event_code') == event_code
    
    return render_template('dashboard.html', event=event.to_dict(), is_creator=is_creator)

@app.route('/match_guests/<event_code>')
def match_guests(event_code):
    if 'event_code' not in session or session['event_code'] != event_code:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))
    
    event = events.get(event_code)
    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('index'))
    
    share_link = url_for('register_attendee', share_id=event.share_id, _external=True)
    qr_code_url = event.generate_qr_code(share_link)
    
    return render_template('match_guests.html', event=event.to_dict(), share_link=share_link, qr_code_url=qr_code_url)

@app.route('/register/<share_id>')
def register_attendee(share_id):
    app.logger.debug('Received request to register attendee with share_id: %s', share_id)
    for event in events.values():
        if event.share_id == share_id:
            app.logger.debug('Found matching event: %s', event.__dict__)
            return render_template('register_attendee.html', event=event.to_dict())
    app.logger.error('No matching event found for share_id: %s', share_id)
    return "Event not found", 404

@app.route('/waiting_room/<event_code>/<attendee_id>')
def waiting_room(event_code, attendee_id):
    if event_code not in events:
        flash('Invalid event code.', 'error')
        return redirect(url_for('index'))
    
    event = events[event_code]
    attendee = next((a for a in event['attendees'] if a['id'] == attendee_id), None)
    
    if not attendee:
        flash('Attendee not found.', 'error')
        return redirect(url_for('register_attendee', event_code=event_code))
    
    return render_template('waiting_room.html', attendee=attendee, event_code=event_code)

@app.route('/match_attendees')
def match_attendees():
    if 'event_code' not in session or session['event_code'] not in events:
        return redirect(url_for('register_attendee'))
    
    event = events[session['event_code']]
    waiting = event['waiting']
    
    # Simple matching algorithm (can be improved)
    while len(waiting) >= 2:
        attendee1_id = waiting.pop(0)
        attendee2_id = waiting.pop(0)
        match = {
            'id': str(uuid.uuid4()),
            'attendees': [attendee1_id, attendee2_id],
            'status': 'active',
            'start_time': time.time()
        }
        event['matches'].append(match)
        
        # Update attendee statuses
        for attendee in event['attendees']:
            if attendee['id'] in [attendee1_id, attendee2_id]:
                attendee['status'] = 'matched'
    
    return redirect(url_for('dashboard'))

@app.route('/extend_match/<match_id>')
def extend_match(match_id):
    if 'event_code' not in session or session['event_code'] not in events:
        return redirect(url_for('register_attendee'))
    
    event = events[session['event_code']]
    match = next((m for m in event['matches'] if m['id'] == match_id), None)
    
    if match:
        match['status'] = 'extended'
        event['extended'].extend(match['attendees'])
        for attendee_id in match['attendees']:
            attendee = next((a for a in event['attendees'] if a['id'] == attendee_id), None)
            if attendee:
                attendee['status'] = 'extended'
    
    return redirect(url_for('dashboard'))

@app.route('/monitor_event', methods=['GET', 'POST'])
def monitor_event():
    if request.method == 'POST':
        event_code = request.form['event_code']
        creator_code = request.form['creator_code']
        event = events.get(event_code)
        if event and event.creator_code == creator_code:
            session['event_code'] = event_code
            return redirect(url_for('dashboard', event_code=event_code))
        else:
            flash('Invalid event code or creator code. Please try again.', 'error')
    
    return render_template('monitor_event.html')

@app.route('/test')
def test():
    return "This is a test route. The time is: " + str(datetime.now())

def send_confirmation_email(event, share_link, qr_code_url):
    msg = Message(f"Your EventMatch Event '{event.name}' Has Been Created",
                  recipients=[event.creator_email])
    
    msg.body = f"""
    Hello {event.creator},

    Your event "{event.name}" has been successfully created on EventMatch.

    Event Details:
    - Event Code: {event.code}
    - Location: {event.location['address']}
    - Radius: {event.radius} km

    You can share this link with your attendees:
    {share_link}

    To access your event dashboard and manage your event, use this link:
    {url_for('dashboard', event_code=event.code, _external=True)}

    To present the QR code for attendees to scan and register, use this link:
    {url_for('match_guests', event_code=event.code, _external=True)}

    Thank you for using EventMatch!
    """

    try:
        mail.send(msg)
        print(f"Confirmation email sent to {event.creator_email}")
    except Exception as e:
        print(f"Error sending email: {e}")
        flash('There was an error sending the confirmation email. Please contact support.', 'error')

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error('Unhandled exception: %s', str(e), exc_info=True)
    return 'An unexpected error occurred', 500

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)