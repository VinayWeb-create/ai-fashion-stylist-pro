# AI Fashion Stylist Pro

**A Wardrobe Decision Assistant** - Not just outfit recommendations, but intelligent wardrobe gap analysis that helps you decide what to buy next and why.

![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![Flask](https://img.shields.io/badge/flask-3.0-red)
![MongoDB](https://img.shields.io/badge/mongodb-4.6+-brightgreen)

---

## 🎯 What Makes This Different

This is **NOT** a shopping site. This is a **Wardrobe Decision Assistant**.

### The Problem
- "I have nothing to wear" despite a full closet
- Buying similar items repeatedly
- No idea what's actually missing from your wardrobe
- Impulse purchases that don't match anything

### Our Solution
- **Digital Wardrobe**: Track what you own
- **Gap Detection**: AI analyzes what's missing and why
- **Impact Ranking**: See how many outfits each item unlocks
- **Smart Recommendations**: Explainable, human-readable advice

---

## ✨ Key Features

### 1. Outfit Recommendations
- Upload any clothing image
- Get 3 ranked outfit suggestions
- Personalized by occasion, climate, body type, budget
- Shopping links to Amazon, Flipkart, Meesho, Myntra

### 2. User Accounts
- Email/password authentication
- Magic link (passwordless) login
- Personal style profile
- Guest mode supported

### 3. Digital Wardrobe
- Save items from recommendations
- Mark items as "already owned"
- Auto-categorization (type, color, occasion, season)
- Visual wardrobe overview

### 4. Wardrobe Intelligence (🔥 KILLER FEATURE)
**Gap Detection Algorithm** that analyzes:
- Missing essentials by occasion
- Color balance (neutrals vs. accents)
- Seasonal coverage
- Category distribution

**For each gap:**
- **What** is missing
- **Why** it matters (plain language)
- **Priority** (high/medium/low)
- **Impact**: How many outfits it unlocks
- **Shopping links** to buy it

### 5. Wardrobe Balance Metrics
- Overall wardrobe score (0-100)
- Occasion readiness (casual, formal, party, ethnic)
- Category distribution
- Season coverage
- Color diversity

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB (local or Atlas)
- pip

### Installation

1. **Clone the repository**
```bash
cd ai-fashion-stylist-pro-frontend-main
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up MongoDB**

**Option A: Local MongoDB**
```bash
# Install MongoDB Community Edition
# Start MongoDB service
mongod --dbpath /path/to/data
```

**Option B: MongoDB Atlas (Cloud - Recommended)**
1. Create free account at [mongodb.com/atlas](https://www.mongodb.com/atlas)
2. Create a cluster (free tier available)
3. Create database user
4. Whitelist IP (0.0.0.0/0 for development)
5. Get connection string

4. **Configure environment variables**
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings
# For MongoDB Atlas:
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
DATABASE_NAME=fashion_stylist
JWT_SECRET_KEY=your-super-secret-key-change-this
```

5. **Run the application**
```bash
python app.py
```

6. **Open in browser**
```
http://localhost:5000
```

---

## 📁 Project Structure

```
ai-fashion-stylist-pro/
├── app.py                      # Main Flask application
├── config.py                   # Configuration management
├── models.py                   # MongoDB models
├── auth.py                     # Authentication (JWT, magic links)
├── wardrobe_intelligence.py    # Gap detection algorithm
├── index.html                  # Frontend
├── script.js                   # Frontend JavaScript
├── style.css                   # Styling
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── DATABASE_SCHEMA.md          # Database documentation
├── API_DOCUMENTATION.md        # API reference
├── PRODUCT_CONCEPT.md          # Product vision
└── README.md                   # This file
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=fashion_stylist

# JWT Secret (CHANGE THIS!)
JWT_SECRET_KEY=your-super-secret-jwt-key

# Email (for magic links - optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@fashionstylist.com

# Application URLs
APP_URL=http://localhost:5000
FRONTEND_URL=http://localhost:5000
```

### Email Setup (Optional)

For magic link authentication:
1. Use Gmail with App Password
2. Or use any SMTP service
3. Leave blank for development (links print to console)

---

## 📖 API Usage

### Authentication

**Register:**
```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "profile": {
      "body_type": "regular",
      "lifestyle": "office",
      "budget_preference": "medium"
    }
  }'
```

**Login:**
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

**Magic Link:**
```bash
curl -X POST http://localhost:5000/auth/magic-link \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

### Wardrobe

**Add Item:**
```bash
curl -X POST http://localhost:5000/wardrobe/add \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Navy Blue Blazer",
    "category": "outerwear",
    "colors": ["Navy Blue"],
    "occasions": ["formal"],
    "season": ["spring", "fall", "winter"],
    "owned": true
  }'
```

**Get Wardrobe:**
```bash
curl -X GET http://localhost:5000/wardrobe/items \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Insights (KILLER FEATURE)

**Get Wardrobe Gaps:**
```bash
curl -X GET http://localhost:5000/insights/gaps \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Get Balance Metrics:**
```bash
curl -X GET http://localhost:5000/insights/balance \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.

---

## 🌐 Deployment

### Railway (Backend)

1. Create account at [railway.app](https://railway.app)
2. Create new project
3. Add MongoDB plugin
4. Deploy from GitHub
5. Set environment variables
6. Deploy!

**Environment Variables for Railway:**
```
MONGODB_URI=<from Railway MongoDB plugin>
DATABASE_NAME=fashion_stylist
JWT_SECRET_KEY=<generate secure key>
APP_URL=<your-railway-url>
FRONTEND_URL=<your-frontend-url>
```

### Render (Backend Alternative)

1. Create account at [render.com](https://render.com)
2. Create Web Service
3. Connect GitHub repo
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python app.py`
6. Add environment variables
7. Deploy!

### Vercel (Frontend)

1. Create account at [vercel.com](https://vercel.com)
2. Import project
3. Set framework preset to "Other"
4. Deploy!

Update `script.js` with your backend URL:
```javascript
const API_URL = 'https://your-backend-url.railway.app/predict';
```

---

## 🧪 Testing

### Manual Testing Checklist

**Guest Mode:**
- [ ] Upload image and get recommendations
- [ ] View shopping links
- [ ] See style tips

**Authentication:**
- [ ] Register new account
- [ ] Login with email/password
- [ ] Request magic link
- [ ] Verify magic link

**Wardrobe:**
- [ ] Add item to wardrobe
- [ ] Mark item as owned
- [ ] View wardrobe items
- [ ] Remove item

**Insights:**
- [ ] View wardrobe gaps
- [ ] See gap explanations
- [ ] Check outfit unlock counts
- [ ] View balance metrics

---

## 🎨 Product Philosophy

### Core Principles

1. **Clarity over Complexity**
   - Simple, human language
   - No fashion jargon
   - Clear explanations

2. **Trust over Sales**
   - User needs first
   - Honest recommendations
   - No dark patterns

3. **Intelligence over Automation**
   - Explainable AI
   - Transparent reasoning
   - User control

4. **Impact over Features**
   - Solve real problems
   - Measurable value
   - Quality over quantity

See [PRODUCT_CONCEPT.md](PRODUCT_CONCEPT.md) for full product vision.

---

## 🗺️ Roadmap

### ✅ MVP (Current)
- Outfit recommendations
- User accounts
- Digital wardrobe
- Gap detection
- Shopping links

### 🚧 V2 (Next 3 months)
- Outfit combination generator
- Social sharing
- Wardrobe photos
- Style quizzes
- Mobile responsive improvements

### 🔮 V3 (6 months)
- Mobile app (React Native)
- Barcode scanning
- Virtual try-on
- Community features
- Sustainability scores

---

## 🤝 Contributing

This is a portfolio/startup project. Contributions welcome!

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 License

This project is open source and available under the MIT License.

---

## 🙏 Acknowledgments

- **Outfit Database**: Curated fashion recommendations
- **E-commerce Platforms**: Amazon, Flipkart, Meesho, Myntra
- **Tech Stack**: Flask, MongoDB, JWT, Vanilla JS

---

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Email: support@fashionstylist.com (placeholder)

---

## 🎯 Key Differentiators

### vs. Shopping Sites
✅ We prioritize user needs over sales  
✅ Focus on "what you need" not "what we sell"  
✅ Trust-based relationship

### vs. Style Apps
✅ Actionable insights, not just inspiration  
✅ Clear explanations for every recommendation  
✅ Wardrobe-aware suggestions

### vs. Personal Stylists
✅ Always available, always free  
✅ Data-driven recommendations  
✅ Scalable to millions

---

## 💡 The Vision

**Transform fashion recommendations from "here's what looks good" to "here's what you actually need and why."**

We're building a product that users return to not because of push notifications, but because it genuinely helps them make better decisions.

**This is a wardrobe decision assistant, not a shopping app.**

---

Made with ❤️ for smarter wardrobe decisions
