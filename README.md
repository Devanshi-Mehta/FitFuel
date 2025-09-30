Health & Fitness Calculator (FastAPI)

A beginner-friendly web app that calculates daily calorie needs and a simple macro breakdown based on your height, weight, age, gender, and activity level.

### Features
- Input form using plain HTML + minimal CSS
- FastAPI backend with clear, well-commented code
- Mifflin-St Jeor BMR, activity multipliers, and simple macro heuristic
- Results page with calories and grams of protein, carbs, and fats

### Requirements
- Python 3.9+

### Quick Start (Windows PowerShell)
```powershell
# 1) Create and activate a virtual environment (recommended)
python -m venv .venv
. .venv\Scripts\Activate.ps1

# 2) Install dependencies
pip install -r requirements.txt

# 3) Run the development server
uvicorn app.main:app --reload

# 4) Open your browser
# Go to http://127.0.0.1:8000
```

If you change code or templates, the `--reload` flag will auto-restart the server.

### Project Structure
```
.
├─ app/
│  └─ main.py            # FastAPI app and calculation logic
├─ templates/
│  ├─ index.html         # Input form page
│  └─ results.html       # Results display page
├─ static/
│  └─ style.css          # Minimal styling
├─ requirements.txt
└─ README.md
```

### Notes on the Calculations
- BMR is computed with the Mifflin-St Jeor equation.
- TDEE is `BMR * activity_multiplier` (sedentary→extra active).
- Macros are set using a simple rule of thumb per kilogram body weight:
  - Protein: 1.8 g/kg
  - Fat: 0.8 g/kg
  - Carbs: remaining calories after protein and fat

Feel free to adjust these numbers to match your goals.

### Deployment
For local learning, `uvicorn` with `--reload` is perfect. To deploy, you can:
- Use a production ASGI server like `uvicorn`/`gunicorn` + `nginx`
- Or containerize with Docker and run on a cloud platform

—
Enjoy learning! The code is heavily commented so you can tweak it easily.


