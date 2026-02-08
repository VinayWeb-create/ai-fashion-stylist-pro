"""
Configuration management for AI Fashion Stylist
Handles MongoDB, JWT, and email settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # MongoDB Configuration
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'fashion_stylist')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24 * 7  # 7 days
    MAGIC_LINK_EXPIRATION_MINUTES = 15
    
    # Email Configuration (for magic links)
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', 'avalavinay8@gmail.com')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'oklp qhob pddx jaup')
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'avalavinay8@gmail.com')
    
    # Application Configuration
    APP_URL= os.getenv('APP_URL', 'https://ai-fashion-stylist-pro-production.up.railway.app/')
    FRONTEND_URL= os.getenv('FRONTEND_URL', 'https://ai-fashion-stylist-pro-frontend.vercel.app/')

    # Security
    BCRYPT_ROUNDS = 12
    
    # Guest Mode
    ALLOW_GUEST_MODE = True
