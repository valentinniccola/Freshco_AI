# 🌿 Freshco AI — Smart Food Freshness Detection & Waste Prevention System

An end-to-end intelligent computer vision platform that analyzes food images using **PyTorch MobileNetV2 CNNs** and **OpenCV** to classify food freshness as **Fresh**, **Nearly Spoiled**, or **Spoiled**, identify specific food types (Apple, Banana, Orange, Mango, Meat, Bakery, etc.), estimate shelf-life windows, and suggest dynamic zero-waste culinary recipes.

---

## 🌟 Key Features

- 📷 **Multi-Source Image Input**: Drag-and-drop file upload, browse gallery, capture live webcam photos, or test pre-loaded sample images.
- 🧠 **Dual PyTorch MobileNetV2 CNN Architecture**:
  - **Freshness Classifier**: Classifies food condition into `Fresh`, `Nearly Spoiled`, or `Spoiled` with calibrated Softmax confidence.
  - **Food-Type Identifier**: Neural multi-class model detecting 12 food types (Apple, Banana, Orange, Mango, Tomato, Strawberry, Meat, Bakery, etc.) with defensive Dairy/Bakery category fallback.
- 🔬 **Explainable OpenCV Colorimetry**: LAB/HSV defect segmentation, Browning Index (0–10), Spot/Decay Coverage %, and texture homogeneity analysis.
- ⏳ **Predictive Shelf-Life & Storage Guidance**: Heuristic engine calculating remaining usable days and tailored temperature/airtight storage advice.
- 🍳 **Zero-Waste Recipe Recommendation Engine**: Automatically matches Nearly Spoiled produce with creative recipes (e.g. Banana Bread, Citrus Marmalade, Compotes) to prevent domestic food waste.
- 📊 **Historical Analytics Dashboard**: SQLite-backed scan history with daily volume trends, food waste reduction ratios, and category breakdowns.
- 🔐 **Enterprise Security & 2-Step OTP Reset**: JWT Bearer token authentication, salted Bcrypt password hashing, optional phone registration, and 6-digit Gmail SMTP email verification codes.
- 🌓 **Modern Dual Theme UI**: High-contrast Dark and Light themes built with React 19, Vite 8, Tailwind CSS v4, Lucide icons, and Recharts.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 19, Vite 8, Tailwind CSS v4, Lucide React, Recharts, Axios, Canvas Confetti |
| **Backend API** | Python 3, FastAPI, Uvicorn ASGI, Pydantic v2 Settings, Sliding Rate Limiter |
| **AI / Computer Vision** | PyTorch, Torchvision MobileNetV2, OpenCV (`cv2`), NumPy, Pillow, Scikit-learn |
| **Database & ORM** | SQLite 3, SQLAlchemy 2.0 ORM, Automated Programmatic Migrations |
| **Authentication & Mail** | PyJWT (Tokens), Bcrypt (Hashing), Gmail SMTP TLS (Verification Codes) |

---

## 📁 Project Structure

```
Freshco_AI/
├── backend/
│   ├── ai/
│   │   ├── models/                    # Trained MobileNetV2 PyTorch & Joblib weights
│   │   ├── food_classifier.py         # 12-Class Food-Type CNN & defensive routing
│   │   ├── model.py                   # Freshness MobileNetV2 CNN inference engine
│   │   ├── preprocessor.py            # OpenCV defect masking, browning, LAB metrics
│   │   ├── recipe_service.py          # Zero-Waste Recipe Recommendation Engine
│   │   ├── shelf_life.py              # Dynamic Shelf-Life & storage advisor
│   │   ├── train_food_type_cnn.py     # Multi-class Food-Type training pipeline
│   │   └── train_mobilenet_cnn.py     # Freshness CNN training pipeline
│   ├── migrations/
│   │   └── migrate_db.py              # Non-destructive schema migration runner
│   ├── routers/
│   │   ├── auth.py                    # /api/auth (Register, Login, OTP Password Reset)
│   │   ├── history.py                 # /api/history (Scan logs & aggregated analytics)
│   │   └── predict.py                 # /api/predict (Multi-stage validation & inference)
│   ├── static/samples/                # Pre-bundled sample food images
│   ├── auth.py                        # JWT security utilities & Bcrypt hashing
│   ├── config.py                      # Pydantic Settings & environment loader
│   ├── database.py                    # SQLAlchemy database engine & session maker
│   ├── email_service.py               # Gmail SMTP HTML email delivery service
│   ├── main.py                        # FastAPI main application entrypoint
│   ├── models.py                      # SQLAlchemy models (User, Prediction, ResetCode)
│   ├── rate_limiter.py                # In-memory sliding window rate limiters
│   ├── schemas.py                     # Pydantic v2 validation schemas
│   └── requirements.txt               # Backend Python dependencies
├── frontend/
│   ├── public/                        # Static web assets and icons
│   ├── src/
│   │   ├── components/                # React UI components (Scanner, AuthModal, Analytics, etc.)
│   │   ├── context/                   # React Contexts (AuthContext, ThemeContext)
│   │   ├── services/                  # Axios REST API client & interceptors
│   │   ├── App.jsx                    # Main layout container
│   │   └── index.css                  # Tailwind CSS styling & animations
│   ├── package.json                   # Frontend npm dependencies
│   └── vite.config.js                 # Vite bundler configuration
├── sample_uploads/                    # Cataloged sample test images across categories
├── Freshco_AI_Presentation.pptx       # 5-page widescreen project presentation deck
├── run_app.py                         # Unified concurrent launcher script
├── .gitignore                         # Standard git ignore rules
└── README.md                          # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.10 – 3.14)
- **Node.js 18+** and **npm**

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
```

*(Optional)* Configure your email credentials in `backend/.env`:
```env
SECRET_KEY=your-secret-key-here
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
```

Start the FastAPI server:
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
- **API URL**: `http://127.0.0.1:8000`
- **Swagger Docs**: `http://127.0.0.1:8000/docs`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- **Web App**: `http://127.0.0.1:5173`

---

## 🔄 End-to-End System Flow

```
[ User Input: File / Camera ]
             │
             ▼
[ React 19 Frontend + Axios ]
             │ (POST /api/predict)
             ▼
[ FastAPI Backend: Multi-Stage Validation Pipeline ]
             │
             ├─► 1. File & Blur Validation (Resolution ≥224x224, Laplacian variance)
             ├─► 2. OpenCV Colorimetry (LAB/HSV Browning Index, Spot Coverage %)
             ├─► 3. MobileNetV2 CNN Inference (Fresh / Nearly Spoiled / Spoiled)
             ├─► 4. Food-Type Classifier (Apple, Banana, Orange, Meat, Bakery, etc.)
             ├─► 5. Dynamic Shelf-Life Engine (Estimated days remaining & storage tips)
             ├─► 6. Zero-Waste Recipe Engine (Matched for Nearly Spoiled produce)
             │
             ▼
[ Interactive Results Dashboard & SQLite Persistent Scan Logs ]
```

---

## ⚠️ Disclaimer
Freshco AI identifies visual optical signs of surface degradation, oxidative browning, discoloration, and mold. It cannot detect invisible bacterial foodborne pathogens. Outputs are AI-assisted recommendations and should be combined with standard food safety practices.
