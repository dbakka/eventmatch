# MatchMaker

MatchMaker is a web application that helps event organizers create and manage networking events, facilitating connections between attendees.

## Features

- Create and manage events
- Generate unique QR codes for event registration
- Match attendees based on preferences
- Real-time updates for event status

## Technologies Used

- Python
- Flask
- HTML/CSS
- JavaScript
- Heroku for deployment

## Setup and Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (see `.env.example`)
4. Run the application: `python app.py`

## Usage

1. Creating an Event:
   - Navigate to the homepage and click "Create Event"
   - Fill in the event details (name, location, radius, etc.)
   - Submit the form to create your event

2. Sharing the Event:
   - After creating an event, you'll receive a unique event code and QR code
   - Share this code or QR code with potential attendees

3. Attendee Registration:
   - Attendees can register by scanning the QR code or entering the event code
   - They'll be prompted to fill in their details and preferences

4. Managing the Event:
   - As an event organizer, access your event dashboard using the event code
   - View registered attendees and monitor event status

5. Matching Process:
   - When ready, initiate the matching process from the dashboard
   - The system will pair attendees based on their preferences

6. During the Event:
   - Attendees can view their matches and initiate conversations
   - They can request new matches if desired

7. Post-Event:
   - Access post-event analytics from the dashboard
   - Gather feedback from attendees for future improvements

Note: Ensure you have a stable internet connection for real-time updates and smooth operation of the application.

## Contributing


## License

[Specify the license under which your project is released]

## Contact

[David Bakka] - [davitenbakka@gmail.com]

Project Link: [https://github.com/dbakka/MatchMaker](https://github.com/dbakka/MatchMaker)
