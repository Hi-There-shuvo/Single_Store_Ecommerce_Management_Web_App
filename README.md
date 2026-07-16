# 🛒 SoloStore — Single Store E-Commerce Management Web App

<div align="center">

![Django](https://img.shields.io/badge/Django-6.0.4-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/Neon-PostgreSQL-00E5FF?style=for-the-badge&logo=postgresql&logoColor=white)
![Cloudinary](https://img.shields.io/badge/Cloudinary-Media_Storage-3448C5?style=for-the-badge&logo=cloudinary&logoColor=white)
![Render](https://img.shields.io/badge/Render-Live_Deploy-46E3B7?style=for-the-badge&logo=render&logoColor=white)
![Stripe](https://img.shields.io/badge/Stripe-Payments-635BFF?style=for-the-badge&logo=stripe&logoColor=white)

**A full-featured, production-ready single-vendor e-commerce platform built with Django.**

[🌐 Live Demo](https://single-store-ecommerce-management-web-app.onrender.com) • [📦 Repository](https://github.com/Hi-There-shuvo/Single_Store_Ecommerce_Management_Web_App)

</div>

---

## ✨ Features

### 🛍️ Customer Side
- **Product Browsing** — Browse products by category with search functionality
- **Flash Sales** — Time-limited discount deals with countdown timers
- **Shopping Cart** — Session-based cart with quantity management
- **Secure Checkout** — Stripe-powered online payment integration
- **Order Tracking** — View order history and real-time status updates
- **User Profile** — Update personal info, address, and profile picture (Cloudinary)
- **Star Reviews** — Leave ratings and reviews on purchased products

### ⚙️ Admin Dashboard
- **Analytics Overview** — Revenue, profit, orders, top-selling products at a glance
- **Product Management** — Add/edit/delete products with multiple images
- **Category Management** — Organize products into categories with icons
- **Order Management** — Filter by status (Pending / Processing / Shipped / Delivered / Cancelled)
- **User Management** — View all customers, spending history, top buyer highlight
- **Low Stock Alerts** — Automatically flags products running low
- **Flash Sale Manager** — Create and manage time-based sales
- **Review Moderation** — View and manage customer reviews
- **Store Settings** — Customize store name, logo, contact info

### 🔐 Authentication
- User Registration & Login
- Password Reset via Email
- Password visibility toggle
- Session management

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 6.0.4 (Python) |
| **Database** | Neon PostgreSQL (Production) / SQLite (Development) |
| **Media Storage** | Cloudinary |
| **Static Files** | WhiteNoise |
| **Payments** | Stripe |
| **Hosting** | Render |
| **Frontend** | HTML5, CSS3 (Vanilla), JavaScript |
| **Web Server** | Gunicorn |

---

## 🚀 Live Demo

> 🌐 **[https://single-store-ecommerce-management-web-app.onrender.com](https://single-store-ecommerce-management-web-app.onrender.com)**

> ⚠️ **Note:** Hosted on Render's free tier — the server may take **30–60 seconds** to wake up after inactivity. Please be patient on first load.

---

## ⚙️ Local Development Setup

### Prerequisites
- Python 3.11+
- pip
- Git

### 1. Clone the repository
```bash
git clone https://github.com/Hi-There-shuvo/Single_Store_Ecommerce_Management_Web_App.git
cd Single_Store_Ecommerce_Management_Web_App
```

### 2. Create and activate virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 5. Run migrations
```bash
python manage.py migrate
```

### 6. Create superuser
```bash
python manage.py createsuperuser
```

### 7. Run the development server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` 🎉

---

## 🔑 Environment Variables

Create a `.env` file in the project root (see `.env.example`):

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Neon PostgreSQL (leave empty to use local SQLite)
DATABASE_URL=postgresql://...

# Cloudinary (leave empty to use local media folder)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
```

---

## 📁 Project Structure

```
ecommerce_project/
├── accounts/          # User auth, registration, profile
├── cart/              # Shopping cart (session-based)
├── dashboard/         # Admin dashboard & analytics
├── orders/            # Order management & Stripe checkout
├── store/             # Products, categories, reviews, flash sales
├── templates/         # All HTML templates
├── static/            # CSS, JavaScript, assets
├── single_store_ecommerce/  # Project settings & URLs
├── build.sh           # Render build script
├── render.yaml        # Render deployment config
├── requirements.txt   # Python dependencies
└── .env.example       # Environment variable template
```

---

## 🌐 Deployment

This project is deployed on **Render** with:
- **Database:** [Neon](https://neon.tech) (Serverless PostgreSQL)
- **Media:** [Cloudinary](https://cloudinary.com) (Image CDN)
- **Static Files:** WhiteNoise (served via Gunicorn)
- **Build:** Automatic via `build.sh` on every GitHub push

---

## 📄 License

This project is built for educational purposes as part of a CSE-3100 course project.

---

<div align="center">

Made with ❤️ by **Mia Shuvo**

⭐ Star this repo if you found it helpful!

</div>
