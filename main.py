"""
FastAPI application for a simple health & fitness calculator.

This app exposes two routes:
- GET "/": Renders the input form
- POST "/calculate": Accepts user inputs, computes daily calories and macros, then shows results

The code is intentionally verbose and well-commented for beginners.
"""

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import json
import os
from pathlib import Path
from datetime import datetime


app = FastAPI(title="Health & Fitness Calculator")

# Mount the static directory for serving CSS/JS/images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Jinja2 templates (HTML files live in the "templates" directory)
templates = Jinja2Templates(directory="templates")

# Location for simple JSON persistence. For a real app, consider a database instead.
DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "users.json"


def _ensure_data_file_exists() -> None:
    """Create the data directory and file if they do not exist."""
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")


def load_users() -> list:
    """Load the list of saved user entries from JSON storage.

    Returns a list of dicts. If the file is empty or invalid, return an empty list.
    """
    _ensure_data_file_exists()
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_user_entry(entry: dict) -> None:
    """Append a single user entry to the JSON file in a safe, simple way."""
    _ensure_data_file_exists()
    data = load_users()
    data.append(entry)
    # Write back to disk. Using indent for readability if you open the file.
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def calculate_bmr_mifflin_st_jeor(weight_kg: float, height_cm: float, age_years: int, gender: str) -> float:
    """Calculate Basal Metabolic Rate (BMR) using the Mifflin-St Jeor equation.

    - weight_kg: Body weight in kilograms
    - height_cm: Height in centimeters
    - age_years: Age in years (integer)
    - gender: "male" or "female"

    Returns the estimated BMR (calories/day).
    """
    # Mifflin-St Jeor equations:
    # Male:   BMR = 10*weight + 6.25*height - 5*age + 5
    # Female: BMR = 10*weight + 6.25*height - 5*age - 161
    base = 10.0 * weight_kg + 6.25 * height_cm - 5.0 * age_years
    if gender.lower() == "male":
        return base + 5.0
    else:
        # Treat any non-"male" value as female for simplicity
        return base - 161.0


def activity_multiplier(level: str) -> float:
    """Map a human-friendly activity level string to a numeric multiplier.

    These are common estimates used by many calculators:
    - sedentary: little/no exercise (x1.2)
    - light: light exercise 1-3 days/week (x1.375)
    - moderate: moderate exercise 3-5 days/week (x1.55)
    - very: hard exercise 6-7 days/week (x1.725)
    - extra: very hard exercise/physical job (x1.9)
    """
    mapping = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "very": 1.725,
        "extra": 1.9,
    }
    return mapping.get(level, 1.2)  # Default to sedentary if unknown


def compute_macros(total_calories: float, weight_kg: float) -> dict:
    """Compute daily macros (protein, fat, carbs) from total calories.

    Approach (simple and beginner-friendly):
    - Protein: 1.8 g per kg body weight (common target for active individuals)
    - Fat: 0.8 g per kg body weight (ensures essential fat intake)
    - Carbs: whatever calories remain after protein and fat

    Energy densities:
    - Protein: 4 kcal/g
    - Carbs: 4 kcal/g
    - Fat: 9 kcal/g
    """
    protein_grams = 1.8 * weight_kg
    fat_grams = 0.8 * weight_kg

    protein_cal = protein_grams * 4.0
    fat_cal = fat_grams * 9.0

    remaining_cal_for_carbs = max(total_calories - (protein_cal + fat_cal), 0.0)
    carb_grams = remaining_cal_for_carbs / 4.0

    return {
        "protein_g": protein_grams,
        "fat_g": fat_grams,
        "carb_g": carb_grams,
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the input form page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/calculate", response_class=HTMLResponse)
async def calculate(
    request: Request,
    name: str = Form("", description="Optional user display name"),
    height_cm: float = Form(..., description="Height in centimeters"),
    weight_kg: float = Form(..., description="Weight in kilograms"),
    age_years: int = Form(..., description="Age in years"),
    gender: str = Form(..., description='"male" or "female"'),
    activity_level: str = Form(..., description="Activity level key"),
    save: str | None = Form(None, description="If provided, save this entry"),
):
    """Handle form submission, perform calculations, and render the results page.

    Steps:
    1) Compute BMR with Mifflin-St Jeor
    2) Multiply BMR by activity factor to get Total Daily Energy Expenditure (TDEE)
    3) Split TDEE into macros using a simple heuristic
    4) Render results
    """
    # 1) BMR
    bmr = calculate_bmr_mifflin_st_jeor(weight_kg, height_cm, age_years, gender)

    # 2) TDEE = BMR * activity factor
    multiplier = activity_multiplier(activity_level)
    tdee = bmr * multiplier

    # 3) Macro breakdown (in grams)
    macros = compute_macros(total_calories=tdee, weight_kg=weight_kg)

    # Prepare values for display: round for nicer presentation
    result = {
        "calories": round(tdee),
        "protein_g": round(macros["protein_g"]),
        "fat_g": round(macros["fat_g"]),
        "carb_g": round(macros["carb_g"]),
        # Also surface some intermediate values so you can inspect them later
        "bmr": round(bmr),
        "activity_multiplier": multiplier,
    }

    # Optionally persist the entry when the user checked "Save my details"
    if save is not None:
        entry = {
            "name": name or "Anonymous",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "inputs": {
                "height_cm": height_cm,
                "weight_kg": weight_kg,
                "age_years": age_years,
                "gender": gender,
                "activity_level": activity_level,
            },
            "results": result,
        }
        save_user_entry(entry)

    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "result": result,
            "inputs": {
                "name": name,
                "height_cm": height_cm,
                "weight_kg": weight_kg,
                "age_years": age_years,
                "gender": gender,
                "activity_level": activity_level,
            },
            "saved": save is not None,
        },
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Simple dashboard listing all saved user entries."""
    users = load_users()
    # Newest first for convenience
    users_sorted = sorted(users, key=lambda u: u.get("timestamp", ""), reverse=True)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "users": users_sorted},
    )

def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # dynamic port
    uvicorn.run(app, host="0.0.0.0", port=port)


