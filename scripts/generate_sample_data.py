# Synthetic grievance dataset generator with intentional municipal spikes.

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

random.seed(42)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEPARTMENTS = [
    "Water Supply",
    "Sanitation",
    "Electrical",
    "Roads",
    "Streetlights",
    "Education",
    "Health",
    "Revenue",
    "Forest",
]

WARDS = [f"Ward {i}" for i in range(1, 13)]

TEMPLATES = {
    "Water Supply": [
        "No water supply in {ward} since last 3 days. The overhead tank is overflowing but "
        "no water reaching houses in lane 3.",
        "Contaminated drinking water being pumped into our residential area in {ward}. It "
        "has bad odor and muddy color.",
        "Underground pipeline burst near main junction in {ward}. Potable water is flooding "
        "the street for 24 hours.",
        "Extremely low water pressure in {ward}. Even motors cannot lift water to storage "
        "tanks on first floor.",
        "Public water tap broken near community center in {ward}, wasting hundreds of "
        "liters daily.",
    ],
    "Sanitation": [
        "Garbage not collected for 1 week in {ward}. Smell is unbearable and stray animals "
        "are scattering waste everywhere.",
        "Open sewage drain overflowing across the walking street in {ward}. Mosquito "
        "breeding hazard.",
        "Public dustbins overflowing and damaged near market area in {ward}. Need immediate "
        "clearing.",
        "Dead animal lying on roadside in {ward} causing severe foul smell and health hazard.",
        "Sanitation workers have not swept the residential colony in {ward} for over two weeks.",
    ],
    "Electrical": [
        "Frequent power tripping and voltage fluctuation in {ward} damaging household "
        "refrigerators and fans.",
        "Transformer sparking intermittently during evening peak hours in {ward}. Sparks "
        "falling near shops.",
        "Hanging live electric wire dangerously low across the school lane in {ward}.",
        "Power outage lasting more than 8 hours without prior notice in {ward}.",
        "Electric pole tilted dangerously after storm in {ward}, risk of collapse.",
    ],
    "Roads": [
        "Deep potholes on main bus route in {ward} causing frequent two-wheeler accidents.",
        "Road dug up for pipeline work in {ward} left unpaved and open for over a month.",
        "Speed breaker missing near school crossing in {ward} where vehicles overspeed "
        "dangerously.",
        "Waterlogging on road after brief rain in {ward} due to lack of storm water gradient.",
        "Tar road completely eroded exposing sharp gravel stones in {ward}.",
    ],
    "Streetlights": [
        "Street light near primary school has been broken for 2 months in {ward}. Children "
        "walk in darkness during winter mornings.",
        "All streetlights on lane 4 in {ward} stay on during daytime and switch off at night.",
        "Dark stretch of 500 meters along canal road in {ward} due to non-functional sodium lamps.",
        "New LED street lights flickering continuously causing glare and headache in {ward}.",
        "Underground cable fault knocked out entire street lighting grid in {ward}.",
    ],
    "Education": [
        "Government primary school in {ward} lacks clean drinking water facility for students.",
        "Boundary wall of municipal school collapsed in {ward}, stray cattle entering premises.",
        "No ceiling fans working in class 5 classroom during summer heat in {ward}.",
    ],
    "Health": [
        "Primary health center in {ward} has severe shortage of essential fever medicines "
        "and ORS packets.",
        "Anti-larval fogging not carried out in {ward} despite multiple reported dengue cases.",
        "Ambulance parking blocked by unauthorized vendors near clinic in {ward}.",
    ],
    "Revenue": [
        "Property tax assessment receipt not generated despite online payment deduction in {ward}.",
        "Delay in issuing trade license renewal certificate from zonal revenue office for {ward}.",
    ],
    "Forest": [
        "Overgrown tree branches touching high-tension power lines near house number 45 in {ward}.",
        "Dry eucalyptus tree leaning towards residential roof in {ward}, requires emergency "
        "pruning.",
    ],
}


def generate_complaint_text(dept: str, ward: str) -> str:
    """Select a template, inject location, and add human variations."""
    templates = TEMPLATES.get(dept, TEMPLATES["Water Supply"])
    tpl = random.choice(templates)
    text = tpl.format(ward=ward)

    # Add realistic variations and citizen tone
    intros = [
        "",
        "Respected Municipal Commissioner, ",
        "Urgent complaint: ",
        "Kindly note that ",
        "Sir, bringing to your immediate notice: ",
    ]
    closings = [
        "",
        " Please take prompt action.",
        " Citizens are suffering greatly.",
        " Repeated complaints to ward councillor have gone unheard.",
        " Immediate inspection requested.",
    ]
    return f"{random.choice(intros)}{text}{random.choice(closings)}"


def main():
    """Generate 1,200 synthetic complaints spanning 8 weeks with intentional anomaly spikes."""
    end_date = datetime(2026, 3, 20)
    complaints = []
    current_id = 1

    # Generate historical background distribution across 8 weeks (Weeks 1 to 6: ~120/wk)
    for week_offset in range(7, 1, -1):
        week_start = end_date - timedelta(weeks=week_offset)
        for _ in range(125):
            dept = random.choice(DEPARTMENTS)
            ward = random.choice(WARDS)
            day_offset = random.randint(0, 6)
            f_date = (week_start + timedelta(days=day_offset)).strftime("%Y-%m-%d")

            complaints.append(
                {
                    "id": current_id,
                    "text": generate_complaint_text(dept, ward),
                    "ward": ward,
                    "department": dept,
                    "category": dept,
                    "filed_date": f_date,
                    "is_synthetic": True,
                }
            )
            current_id += 1

    # Active period: Weeks 7 and 8 (Inject deliberate statistical spikes)
    # 1. Primary Spike: Water Supply in Ward 4 (+340% surge, 65 complaints vs baseline 15)
    # 2. Secondary Spike: Sanitation / Waste in Ward 7 (+210% surge)
    # 3. Tertiary Spike: Streetlights in Ward 5 (+180% surge)
    for week_offset in [1, 0]:
        week_start = end_date - timedelta(weeks=week_offset)

        # Baseline noise for week
        for _ in range(110):
            dept = random.choice(DEPARTMENTS)
            ward = random.choice(WARDS)
            day_offset = random.randint(0, 6)
            f_date = (week_start + timedelta(days=day_offset)).strftime("%Y-%m-%d")
            complaints.append(
                {
                    "id": current_id,
                    "text": generate_complaint_text(dept, ward),
                    "ward": ward,
                    "department": dept,
                    "category": dept,
                    "filed_date": f_date,
                    "is_synthetic": True,
                }
            )
            current_id += 1

        # Injected Spike 1: Water Supply in Ward 4 (35 per week = 70 total surge)
        for _ in range(35):
            day_offset = random.randint(0, 6)
            f_date = (week_start + timedelta(days=day_offset)).strftime("%Y-%m-%d")
            complaints.append(
                {
                    "id": current_id,
                    "text": generate_complaint_text("Water Supply", "Ward 4"),
                    "ward": "Ward 4",
                    "department": "Water Supply",
                    "category": "Water Supply",
                    "filed_date": f_date,
                    "is_synthetic": True,
                }
            )
            current_id += 1

        # Injected Spike 2: Sanitation in Ward 7 (20 per week)
        for _ in range(20):
            day_offset = random.randint(0, 6)
            f_date = (week_start + timedelta(days=day_offset)).strftime("%Y-%m-%d")
            complaints.append(
                {
                    "id": current_id,
                    "text": generate_complaint_text("Sanitation", "Ward 7"),
                    "ward": "Ward 7",
                    "department": "Sanitation",
                    "category": "Sanitation",
                    "filed_date": f_date,
                    "is_synthetic": True,
                }
            )
            current_id += 1

        # Injected Spike 3: Streetlights in Ward 5 (16 per week)
        for _ in range(16):
            day_offset = random.randint(0, 6)
            f_date = (week_start + timedelta(days=day_offset)).strftime("%Y-%m-%d")
            complaints.append(
                {
                    "id": current_id,
                    "text": generate_complaint_text("Streetlights", "Ward 5"),
                    "ward": "Ward 5",
                    "department": "Streetlights",
                    "category": "Streetlights",
                    "filed_date": f_date,
                    "is_synthetic": True,
                }
            )
            current_id += 1

    # Trim or pad to exactly 1,200 records
    complaints = complaints[:1200]
    while len(complaints) < 1200:
        complaints.append(
            {
                "id": len(complaints) + 1,
                "text": generate_complaint_text("Roads", "Ward 1"),
                "ward": "Ward 1",
                "department": "Roads",
                "category": "Roads",
                "filed_date": end_date.strftime("%Y-%m-%d"),
                "is_synthetic": True,
            }
        )

    # Save JSON
    json_path = DATA_DIR / "sample_complaints.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(complaints, f, indent=2)

    # Save CSV
    csv_path = DATA_DIR / "sample_complaints.csv"
    df = pd.DataFrame(complaints)
    df.to_csv(csv_path, index=False)

    print(f"Generated {len(complaints)} synthetic complaints.")
    print(f"Saved JSON: {json_path}")
    print(f"Saved CSV:  {csv_path}")


if __name__ == "__main__":
    main()
