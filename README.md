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

## Recent Updates - Band Scoring System

### New Band Scoring System
The band scoring system has been updated to better align with the "one band per user" rule and subscription-based benefits:

#### Key Changes:
1. **One Band Only**: Users can now only be in one band at a time (either as creator or member)
2. **Simplified Scoring**: Replaced total_bands, total_score, and average_score with a single overall_score
3. **Subscription-Based Bonuses**: Users with active "Bands" subscription get significant scoring benefits

#### Scoring Components:
- **Base Score** (up to 60 points): Profile completion (30) + Media content (30)
- **Subscription Bonus** (40 points): Active "Bands" plan subscription
- **Profile Completion Bonus** (20 points): Complete band profile information
- **Maximum Score**: 100 points

#### How to Improve Band Score:
1. **Subscribe to Bands Plan** (+40 points) - Biggest impact
2. **Complete Band Profile** (+20 bonus points when 100% complete)
3. **Add Media Content** (up to +30 points for photos/videos)
4. **Invite Band Members** (improves visibility)

#### API Response Example:
```json
{
  "bands": [...],
  "band_score": {
    "overall_score": 85,
    "has_bands_subscription": true,
    "user_role": "creator",
    "score_breakdown": {
      "base_score": 45,
      "subscription_bonus": 40,
      "profile_completion_bonus": 0,
      "details": {...}
    },
    "how_to_improve": ["Complete all band profile information for +20 bonus points"],
    "message": "You are a creator of 'My Band' band"
  }
}
```

#### Restrictions:
- Users can only create one band
- Users can only join one band at a time
- Must leave current band before joining/creating another 