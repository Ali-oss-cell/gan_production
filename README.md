# Talent Platform

A comprehensive platform for connecting talents with opportunities, featuring advanced search and matching capabilities.

## Features

- Talent profile management (Visual, Expressive, and Hybrid workers)
- Advanced search and filtering system
- Genre-based dynamic forms
- Skill verification system
- Subscription plans (Silver, Gold, Platinum)
- Background jobs management

## Tech Stack

- Django
- Django REST Framework
- PostgreSQL
- Stripe (for payments)
- ImageKit (for media handling)
- FFmpeg (for video processing)

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL
- FFmpeg
- Stripe account

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/talent-platform.git
cd talent-platform
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with the following variables:
```
DEBUG=True
SECRET_KEY=your_secret_key
DATABASE_URL=postgres://user:password@localhost:5432/dbname
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Start the development server:
```bash
python manage.py runserver
```

## Project Structure

```
talent_platform/
├── profiles/           # Talent profile management
├── payments/          # Payment and subscription handling
├── media/            # Media file handling
├── static/           # Static files
└── templates/        # HTML templates
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 