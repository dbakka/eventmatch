from typing import List, Dict, Tuple
import random
import string
import qrcode
import io
import base64
from geopy.geocoders import Nominatim
from flask import request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any
import uuid

class Event:
    def __init__(self, name: str, location: Dict[str, Any], creator: str, creator_email: str, radius: float = 5.0):
        self.name = name
        self.location = location  # Now includes 'address' key
        self.creator = creator
        self.creator_email = creator_email
        self.radius = radius
        self.code = self.generate_unique_code()
        self.share_id = str(uuid.uuid4())[:8]  # Generate a short UUID for sharing
        self.questions = []
        self.attendees = []

    @staticmethod
    def generate_unique_code():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def generate_qr_code(self, data):
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

    def add_question(self, question: str):
        self.questions.append(question)

    def add_attendee(self, attendee: 'Attendee'):
        self.attendees.append(attendee)

    def send_code_to_creator(self, registration_url):
        # Implement email sending logic here
        pass

    def to_dict(self):
        return {
            'name': self.name,
            'location': self.location,
            'creator': self.creator,
            'creator_email': self.creator_email,
            'radius': self.radius,
            'code': self.code,
            'share_id': self.share_id,
            'questions': self.questions,
            'attendees': self.attendees
        }

class Attendee:
    def __init__(self, name: str, details: Dict[str, str]):
        self.name = name
        self.details = details
        self.answers = {}

class MatchMaker:
    def __init__(self, event: Event):
        self.event = event

    def calculate_compatibility(self, attendee1: Attendee, attendee2: Attendee) -> float:
        # Simple compatibility calculation (random for this example)
        return random.random()

    def pair_attendees(self) -> List[Tuple[Attendee, Attendee]]:
        pairs = []
        available_attendees = self.event.attendees.copy()
        
        while len(available_attendees) >= 2:
            attendee1 = available_attendees.pop(0)
            best_match = max(available_attendees, key=lambda a: self.calculate_compatibility(attendee1, a))
            available_attendees.remove(best_match)
            pairs.append((attendee1, best_match))

        return pairs

    def generate_conversation_starters(self, pair: Tuple[Attendee, Attendee]) -> List[str]:
        # Simple conversation starter generation
        return [
            "What's the most interesting project you're working on right now?",
            "What brought you to this event today?",
            "What's your favorite part about your job/studies?"
        ]

    def verify_attendee_location(self, ip_address: str) -> bool:
        # Implement geolocation verification logic here
        # For example, using the requests library and an IP geolocation API
        # ...
        return True