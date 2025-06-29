# Event Scheduler System
# A complete Flask REST API for managing events with persistence and advanced features

from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import json
import os
import threading
import time
import re
from typing import Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

class EventScheduler:
    def __init__(self, data_file='events.json'):
        self.data_file = data_file
        self.events = {}
        self.next_id = 1
        self.load_events()
        self.start_reminder_service()
    
    def load_events(self):
        """Load events from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.events = data.get('events', {})
                    self.next_id = data.get('next_id', 1)
                    # Convert string keys back to integers
                    self.events = {int(k): v for k, v in self.events.items()}
            else:
                self.events = {}
                self.next_id = 1
        except Exception as e:
            print(f"Error loading events: {e}")
            self.events = {}
            self.next_id = 1
    
    def save_events(self):
        """Save events to JSON file"""
        try:
            data = {
                'events': self.events,
                'next_id': self.next_id
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving events: {e}")
    
    def validate_datetime(self, dt_string):
        """Validate datetime format"""
        try:
            return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        except ValueError:
            try:
                return datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return None
    
    def create_event(self, title, description, start_time, end_time, recurring=None):
        """Create a new event"""
        # Validate input
        if not title or not start_time or not end_time:
            return None, "Title, start_time, and end_time are required"
        
        start_dt = self.validate_datetime(start_time)
        end_dt = self.validate_datetime(end_time)
        
        if not start_dt or not end_dt:
            return None, "Invalid datetime format. Use ISO format or 'YYYY-MM-DD HH:MM:SS'"
        
        if start_dt >= end_dt:
            return None, "Start time must be before end time"
        
        event = {
            'id': self.next_id,
            'title': title,
            'description': description or '',
            'start_time': start_dt.isoformat(),
            'end_time': end_dt.isoformat(),
            'recurring': recurring,
            'created_at': datetime.now().isoformat()
        }
        
        self.events[self.next_id] = event
        event_id = self.next_id
        self.next_id += 1
        self.save_events()
        
        return event, None
    
    def get_all_events(self, sort_by='start_time'):
        """Get all events sorted by specified field"""
        events_list = list(self.events.values())
        if sort_by == 'start_time':
            events_list.sort(key=lambda x: x['start_time'])
        return events_list
    
    def get_event(self, event_id):
        """Get a specific event by ID"""
        return self.events.get(event_id)
    
    def update_event(self, event_id, **kwargs):
        """Update an existing event"""
        if event_id not in self.events:
            return None, "Event not found"
        
        event = self.events[event_id].copy()
        
        # Update fields if provided
        if 'title' in kwargs and kwargs['title']:
            event['title'] = kwargs['title']
        if 'description' in kwargs:
            event['description'] = kwargs['description']
        if 'start_time' in kwargs:
            start_dt = self.validate_datetime(kwargs['start_time'])
            if not start_dt:
                return None, "Invalid start_time format"
            event['start_time'] = start_dt.isoformat()
        if 'end_time' in kwargs:
            end_dt = self.validate_datetime(kwargs['end_time'])
            if not end_dt:
                return None, "Invalid end_time format"
            event['end_time'] = end_dt.isoformat()
        if 'recurring' in kwargs:
            event['recurring'] = kwargs['recurring']
        
        # Validate start < end
        start_dt = datetime.fromisoformat(event['start_time'])
        end_dt = datetime.fromisoformat(event['end_time'])
        if start_dt >= end_dt:
            return None, "Start time must be before end time"
        
        event['updated_at'] = datetime.now().isoformat()
        self.events[event_id] = event
        self.save_events()
        
        return event, None
    
    def delete_event(self, event_id):
        """Delete an event"""
        if event_id not in self.events:
            return False, "Event not found"
        
        del self.events[event_id]
        self.save_events()
        return True, None
    
    def search_events(self, query):
        """Search events by title or description"""
        query = query.lower()
        results = []
        for event in self.events.values():
            if (query in event['title'].lower() or 
                query in event['description'].lower()):
                results.append(event)
        
        # Sort by start time
        results.sort(key=lambda x: x['start_time'])
        return results
    
    def get_upcoming_reminders(self):
        """Get events that need reminders (within next hour)"""
        now = datetime.now()
        upcoming = []
        
        for event in self.events.values():
            start_time = datetime.fromisoformat(event['start_time'])
            time_diff = start_time - now
            
            # Check if event is within the next hour
            if timedelta(0) <= time_diff <= timedelta(hours=1):
                upcoming.append({
                    'event': event,
                    'minutes_until': int(time_diff.total_seconds() / 60)
                })
        
        return upcoming
    
    def start_reminder_service(self):
        """Start background service for reminders"""
        def reminder_worker():
            while True:
                try:
                    reminders = self.get_upcoming_reminders()
                    for reminder in reminders:
                        event = reminder['event']
                        minutes = reminder['minutes_until']
                        print(f"REMINDER: '{event['title']}' starts in {minutes} minutes!")
                        print(f"Description: {event['description']}")
                        print(f"Time: {event['start_time']}")
                        print("-" * 50)
                    
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    print(f"Reminder service error: {e}")
                    time.sleep(60)
        
        # Start reminder service in background thread
        reminder_thread = threading.Thread(target=reminder_worker, daemon=True)
        reminder_thread.start()

# Initialize the scheduler
scheduler = EventScheduler()

# Error handler
@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({'error': str(e)}), 500

# Routes
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/events', methods=['POST'])
def create_event():
    """Create a new event"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        event, error = scheduler.create_event(
            title=data.get('title'),
            description=data.get('description'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            recurring=data.get('recurring')
        )
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Event created successfully',
            'event': event
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/events', methods=['GET'])
def get_events():
    """Get all events"""
    try:
        sort_by = request.args.get('sort_by', 'start_time')
        events = scheduler.get_all_events(sort_by=sort_by)
        
        return jsonify({
            'events': events,
            'count': len(events)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """Get a specific event"""
    try:
        event = scheduler.get_event(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        return jsonify({'event': event})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    """Update an existing event"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        event, error = scheduler.update_event(event_id, **data)
        
        if error:
            return jsonify({'error': error}), 400 if error != "Event not found" else 404
        
        return jsonify({
            'message': 'Event updated successfully',
            'event': event
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Delete an event"""
    try:
        success, error = scheduler.delete_event(event_id)
        
        if error:
            return jsonify({'error': error}), 404
        
        return jsonify({'message': 'Event deleted successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/events/search', methods=['GET'])
def search_events():
    """Search events by title or description"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Search query parameter "q" is required'}), 400
        
        results = scheduler.search_events(query)
        
        return jsonify({
            'results': results,
            'count': len(results),
            'query': query
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/events/reminders', methods=['GET'])
def get_reminders():
    """Get upcoming reminders"""
    try:
        reminders = scheduler.get_upcoming_reminders()
        
        return jsonify({
            'reminders': reminders,
            'count': len(reminders)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Event Scheduler API...")
    print("Background reminder service is running...")
    app.run(debug=True, host='0.0.0.0', port=5000)