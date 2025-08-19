# Muni-Info

A WhatsApp chatbot that provides South African citizens with municipal information and services through location-based queries.

## Features

- 📍 **Location Detection**: Automatically identifies municipal boundaries from GPS coordinates
- 🎯 **Complaint Management**: Structured complaint lodging system for municipal issues
- 🚨 **Emergency Services**: Quick access to emergency contact numbers
- 🏛️ **Municipal Information**: Province, district, and local municipality identification
- 💬 **WhatsApp Integration**: Easy-to-use conversational interface

## Project Structure

```
muni-info/
├── src/
│   ├── app.py              # Main Flask application
│   ├── config.py           # Configuration management
│   ├── models/             # Data models
│   │   ├── complaint.py    # Complaint data model
│   │   └── location.py     # Location data model
│   ├── services/           # Business logic
│   │   ├── location_service.py    # Location detection service
│   │   ├── complaint_service.py   # Complaint management service
│   │   └── whatsapp_service.py    # WhatsApp message handling
│   ├── handlers/           # Request handlers
│   │   ├── webhook_handler.py     # WhatsApp webhook handler
│   │   └── api_handler.py         # REST API handler
│   └── utils/              # Utilities
│       ├── state_manager.py       # User conversation state management
│       └── geo_utils.py           # Geospatial utility functions
├── data/                   # Data files
│   ├── za_municipalities.json     # Municipal boundary data
│   └── za_emergency_services.json # Emergency service contacts
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
└── .env.example           # Environment variables template
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd muni-info
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Twilio credentials
```

5. Run the application:
```bash
python main.py
```

## Configuration

Required environment variables:
- `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
- `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token
- `FLASK_ENV`: Environment mode (development/production)

## API Endpoints

### WhatsApp Webhook
- `POST /whatsapp`: Twilio WhatsApp webhook endpoint

### REST API
- `GET /`: Service information
- `POST /locate`: Get municipal information from coordinates

Example locate request:
```json
{
    "latitude": -33.9249,
    "longitude": 18.4241
}
```

## Usage

### WhatsApp Bot Commands
1. Send location to identify your municipality
2. Type "menu" to see available options:
   - View District
   - View Municipality  
   - View Map
   - Lodge Complaint
   - Emergency Services

### Complaint Categories
- Water
- Electricity
- Sanitation
- Roads
- Other

## Dependencies

- **Flask**: Web framework
- **Twilio**: WhatsApp integration
- **Shapely**: Geospatial operations
- **Requests**: HTTP client
- **python-dotenv**: Environment variable management

## External Services

- **MapIt API**: Municipal boundary detection (https://mapit.openup.org.za)
- **Twilio WhatsApp API**: Message delivery and webhook handling

## Contributing

1. Follow the existing code structure and patterns
2. Add appropriate error handling
3. Update tests for new functionality
4. Update documentation as needed