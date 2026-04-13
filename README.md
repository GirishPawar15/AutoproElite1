# AutoPro Elite - Car Marketplace & Spare Parts Management System

## Overview
AutoPro Elite is a comprehensive Django-based platform that combines a car marketplace with spare parts management, billing system, and AI-powered features like chatbot and damage detection.

## Features
- **Car Marketplace**: Browse, list, and purchase cars with admin approval workflow
- **Spare Parts Management**: Complete inventory and POS billing system
- **E-Bill System**: Automated PDF invoice generation and email delivery
- **AI Chatbot**: Gemini AI-powered customer support with local ML fallback
- **Damage Detection**: Car damage analysis using external API
- **Price Prediction**: Intelligent car valuation system
- **User Management**: Profile management with document uploads
- **Analytics Dashboard**: Sales reports, profit analysis, and inventory tracking

## Tech Stack
- **Backend**: Django 5.0+, Django REST Framework
- **Database**: SQLite (development)
- **AI/ML**: Google Gemini API, scikit-learn
- **PDF Generation**: ReportLab
- **Authentication**: Token-based + Google OAuth 2.0
- **Email**: Gmail SMTP integration

## API Endpoints

### Authentication
- `POST /api/auth/signup/` - User registration
- `POST /api/auth/login/` - User login
- `GET /api/auth/google/start/` - Google OAuth initiation
- `GET /api/auth/google/callback/` - Google OAuth callback

### Car Listings
- `GET /api/listings/` - Browse approved listings
- `GET /api/listings/<id>/` - Listing details
- `POST /api/listings/` - Create new listing
- `POST /api/listings/<id>/images/` - Add listing images

### Shopping & Orders
- `GET /api/cart/` - Get cart details
- `POST /api/cart/add/` - Add to cart
- `POST /api/orders/create/` - Create order
- `GET /api/orders/` - User orders

### Billing System
- `POST /api/billing/pos/create/` - Create POS bill
- `GET /api/billing/spare-parts/search/` - Search spare parts
- `GET /api/billing/reports/sales/` - Sales reports (Admin)
- `GET /api/billing/low-stock/` - Low stock alerts (Admin)

### AI Features
- `POST /api/chat/` - Chatbot interaction
- `POST /api/damage/detect/` - Damage detection
- `POST /api/price/predict/` - Price prediction

## Installation & Setup

1. **Clone Repository**
```bash
git clone <repository-url>
cd autopro-elite
```

2. **Create Virtual Environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

4. **Environment Configuration**
Create `.env` file in backend directory:
```env
DJANGO_SECRET_KEY=your-secret-key
GOOGLE_API_KEY=your-gemini-api-key
GOOGLE_CLIENT_ID=your-oauth-client-id
GOOGLE_CLIENT_SECRET=your-oauth-client-secret
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

5. **Database Setup**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

6. **Run Development Server**
```bash
python manage.py runserver
```

## Project Structure
```
backend/
├── ap_backend/          # Django project settings
├── core/                # Main application
│   ├── models.py        # Database models
│   ├── views.py         # API views
│   ├── billing_views.py # Billing system views
│   ├── billing_service.py # Billing business logic
│   ├── ebill_generator.py # PDF generation
│   └── email_utils.py   # Email utilities
├── templates/           # HTML templates
├── static/             # CSS, JS, images
├── media/              # User uploads
└── qna/                # Chatbot ML models
```

## Key Models
- **Listing**: Car listings with approval workflow
- **Order**: Orders for cars and spare parts
- **SparePart**: Inventory management
- **Profile**: Extended user information
- **Cart**: Shopping cart functionality

## Testing
Comprehensive test cases are available in `testcase.readme` covering:
- Authentication flows
- Cart and order management
- Billing system
- AI features
- Admin analytics
- Error handling

## Contributing
1. Fork the repository
2. Create feature branch
3. Run test suite
4. Submit pull request

## License
[Add your license information here]











