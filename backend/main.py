from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, date
import sqlite3
import json
from pathlib import Path
import requests
import csv

app = FastAPI(title="Carbon Footprint Visualizer API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_PATH = "carbon_footprint.db"

# Load KSEB slab rates
def load_kseb_slabs():
    """Load KSEB tiered pricing from CSV"""
    slabs = []
    try:
        with open('kseb_slabs.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                slabs.append({
                    'units_min': int(row['units_min']),
                    'units_max': int(row['units_max']),
                    'rate_per_kwh': float(row['rate_per_kwh']),
                    'slab_description': row['slab_description']
                })
    except FileNotFoundError:
        # Default slab if CSV not found
        slabs = [
            {'units_min': 0, 'units_max': 250, 'rate_per_kwh': 6.50, 'slab_description': '0-250 units'},
            {'units_min': 0, 'units_max': 300, 'rate_per_kwh': 6.50, 'slab_description': '0-300 units'},
            {'units_min': 0, 'units_max': 350, 'rate_per_kwh': 7.60, 'slab_description': '0-350 units'},
            {'units_min': 0, 'units_max': 400, 'rate_per_kwh': 7.60, 'slab_description': '0-400 units'},
            {'units_min': 0, 'units_max': 500, 'rate_per_kwh': 7.60, 'slab_description': '0-500 units'},
            {'units_min': 500, 'units_max': 999999, 'rate_per_kwh': 8.70, 'slab_description': 'above 500 units'}
        ]
    return slabs

KSEB_SLABS = load_kseb_slabs()

# Indian Electricity Board Data
INDIAN_ELECTRICITY_BOARDS = {
    "mseb": {
        "name": "Maharashtra State Electricity Board (MSEB)",
        "state": "Maharashtra",
        "price_per_kwh": 6.5,
        "emission_factor": 0.82,  # kg CO2/kWh
        "grid_mix": {
            "coal": 0.65,
            "renewable": 0.25,
            "gas": 0.08,
            "nuclear": 0.02
        }
    },
    "tneb": {
        "name": "Tamil Nadu Electricity Board (TNEB)",
        "state": "Tamil Nadu",
        "price_per_kwh": 5.8,
        "emission_factor": 0.75,
        "grid_mix": {
            "coal": 0.60,
            "renewable": 0.30,
            "gas": 0.08,
            "nuclear": 0.02
        }
    },
    "bses": {
        "name": "BSES (Delhi)",
        "state": "Delhi",
        "price_per_kwh": 7.2,
        "emission_factor": 0.88,
        "grid_mix": {
            "coal": 0.70,
            "renewable": 0.20,
            "gas": 0.08,
            "nuclear": 0.02
        }
    },
    "tata_power": {
        "name": "Tata Power (Mumbai)",
        "state": "Maharashtra",
        "price_per_kwh": 8.5,
        "emission_factor": 0.85,
        "grid_mix": {
            "coal": 0.68,
            "renewable": 0.22,
            "gas": 0.08,
            "nuclear": 0.02
        }
    },
    "kseb": {
        "name": "Kerala State Electricity Board (KSEB)",
        "state": "Kerala",
        "price_per_kwh": 5.2,
        "emission_factor": 0.45,
        "grid_mix": {
            "coal": 0.30,
            "renewable": 0.60,
            "gas": 0.08,
            "nuclear": 0.02
        }
    },
    "karnataka": {
        "name": "Karnataka Power Corporation (KPC)",
        "state": "Karnataka",
        "price_per_kwh": 6.8,
        "emission_factor": 0.55,
        "grid_mix": {
            "coal": 0.40,
            "renewable": 0.50,
            "gas": 0.08,
            "nuclear": 0.02
        }
    },
    "apspdcl": {
        "name": "Andhra Pradesh Southern Power Distribution Company",
        "state": "Andhra Pradesh",
        "price_per_kwh": 6.2,
        "emission_factor": 0.70,
        "grid_mix": {
            "coal": 0.55,
            "renewable": 0.35,
            "gas": 0.08,
            "nuclear": 0.02
        }
    },
    "gujarat": {
        "name": "Gujarat Urja Vikas Nigam Limited (GUVNL)",
        "state": "Gujarat",
        "price_per_kwh": 6.8,
        "emission_factor": 0.65,
        "grid_mix": {
            "coal": 0.50,
            "renewable": 0.40,
            "gas": 0.08,
            "nuclear": 0.02
        }
    },
    "west_bengal": {
        "name": "West Bengal State Electricity Distribution Company",
        "state": "West Bengal",
        "price_per_kwh": 5.9,
        "emission_factor": 0.90,
        "grid_mix": {
            "coal": 0.75,
            "renewable": 0.15,
            "gas": 0.08,
            "nuclear": 0.02
        }
    },
    "punjab": {
        "name": "Punjab State Power Corporation Limited",
        "state": "Punjab",
        "price_per_kwh": 6.5,
        "emission_factor": 0.80,
        "grid_mix": {
            "coal": 0.65,
            "renewable": 0.25,
            "gas": 0.08,
            "nuclear": 0.02
        }
    }
}

# State to Board mapping for automatic selection
STATE_TO_BOARD = {
    "Maharashtra": "mseb",
    "Tamil Nadu": "tneb",
    "Delhi": "bses",
    "Kerala": "kseb",
    "Karnataka": "karnataka",
    "Andhra Pradesh": "apspdcl",
    "Gujarat": "gujarat",
    "West Bengal": "west_bengal",
    "Punjab": "punjab"
}

def init_db():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Commute logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commute_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            transport_mode TEXT NOT NULL,
            distance_km REAL NOT NULL,
            co2_emissions_kg REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Energy consumption table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS energy_consumption (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            power_consumption_watts REAL NOT NULL,
            duration_hours REAL NOT NULL,
            energy_kwh REAL NOT NULL,
            co2_emissions_kg REAL NOT NULL,
            electricity_board TEXT,
            price_per_kwh REAL,
            cost_rupees REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Monthly aggregations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monthly_aggregations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            total_commute_co2 REAL DEFAULT 0,
            total_energy_co2 REAL DEFAULT 0,
            total_co2 REAL DEFAULT 0,
            commute_distance_km REAL DEFAULT 0,
            energy_consumption_kwh REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(year, month)
        )
    """)
    
    conn.commit()
    conn.close()

# Pydantic models
class CommuteLog(BaseModel):
    date: str
    transport_mode: str
    distance_km: float

class EnergyLog(BaseModel):
    date: str
    power_consumption_watts: float
    duration_hours: float
    electricity_board: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class CommuteLogResponse(BaseModel):
    id: int
    date: str
    transport_mode: str
    distance_km: float
    co2_emissions_kg: float
    created_at: str

class EnergyLogResponse(BaseModel):
    id: int
    date: str
    power_consumption_watts: float
    duration_hours: float
    energy_kwh: float
    co2_emissions_kg: float
    electricity_board: Optional[str]
    price_per_kwh: Optional[float]
    cost_rupees: Optional[float]
    created_at: str

class MonthlyData(BaseModel):
    year: int
    month: int
    total_commute_co2: float
    total_energy_co2: float
    total_co2: float
    commute_distance_km: float
    energy_consumption_kwh: float
    total_energy_cost: float

class ElectricityBoard(BaseModel):
    id: str
    name: str
    state: str
    price_per_kwh: float
    emission_factor: float
    grid_mix: Dict[str, float]

class LocationData(BaseModel):
    latitude: float
    longitude: float

# Carbon footprint calculation functions
def calculate_commute_co2(transport_mode: str, distance_km: float) -> float:
    """Calculate CO2 emissions for different transport modes (kg CO2/km)"""
    emission_factors = {
        "car": 0.192,  # kg CO2/km
        "motorcycle": 0.103,
        "bus": 0.089,
        "train": 0.041,
        "bicycle": 0.0,
        "walking": 0.0,
        "electric_car": 0.053,
        "hybrid_car": 0.120
    }
    return distance_km * emission_factors.get(transport_mode.lower(), 0.1)

def calculate_energy_co2(energy_kwh: float, electricity_board: str = None) -> float:
    """Calculate CO2 emissions for energy consumption (kg CO2/kWh)"""
    if electricity_board and electricity_board in INDIAN_ELECTRICITY_BOARDS:
        emission_factor = INDIAN_ELECTRICITY_BOARDS[electricity_board]["emission_factor"]
    else:
        emission_factor = 0.5  # Default emission factor
    return energy_kwh * emission_factor

def get_location_from_coordinates(latitude: float, longitude: float) -> str:
    """Get state from coordinates using reverse geocoding"""
    try:
        # Using a free reverse geocoding service
        response = requests.get(
            f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={latitude}&longitude={longitude}&localityLanguage=en",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("principalSubdivision", "Unknown")
    except:
        pass
    return "Unknown"

def get_electricity_board_from_location(latitude: float, longitude: float) -> str:
    """Get electricity board based on location"""
    state = get_location_from_coordinates(latitude, longitude)
    return STATE_TO_BOARD.get(state, "mseb")  # Default to MSEB if state not found

def calculate_tiered_cost(energy_kwh: float, electricity_board: str, monthly_consumption: float = 0) -> float:
    """Calculate cost based on tiered pricing for KSEB"""
    if electricity_board == "kseb":
        # For KSEB, use tiered pricing based on monthly consumption
        total_monthly_kwh = monthly_consumption + energy_kwh
        
        # Find the appropriate slab
        applicable_slab = None
        for slab in KSEB_SLABS:
            if total_monthly_kwh >= slab['units_min'] and total_monthly_kwh <= slab['units_max']:
                applicable_slab = slab
                break
        
        if applicable_slab:
            return energy_kwh * applicable_slab['rate_per_kwh']
        else:
            # Default to highest rate if no slab matches
            return energy_kwh * 8.70
    else:
        # For other boards, use flat rate
        board_data = INDIAN_ELECTRICITY_BOARDS.get(electricity_board, INDIAN_ELECTRICITY_BOARDS["mseb"])
        return energy_kwh * board_data["price_per_kwh"]

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def root():
    return {"message": "Carbon Footprint Visualizer API"}

@app.post("/api/commute-logs", response_model=CommuteLogResponse)
async def create_commute_log(log: CommuteLog):
    """Add a new commute log entry"""
    co2_emissions = calculate_commute_co2(log.transport_mode, log.distance_km)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO commute_logs (date, transport_mode, distance_km, co2_emissions_kg)
        VALUES (?, ?, ?, ?)
    """, (log.date, log.transport_mode, log.distance_km, co2_emissions))
    
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return CommuteLogResponse(
        id=log_id,
        date=log.date,
        transport_mode=log.transport_mode,
        distance_km=log.distance_km,
        co2_emissions_kg=co2_emissions,
        created_at=datetime.now().isoformat()
    )

@app.post("/api/energy-logs", response_model=EnergyLogResponse)
async def create_energy_log(log: EnergyLog):
    """Add a new energy consumption log entry"""
    energy_kwh = (log.power_consumption_watts * log.duration_hours) / 1000
    
    # Determine electricity board
    electricity_board = log.electricity_board
    if not electricity_board and log.latitude and log.longitude:
        electricity_board = get_electricity_board_from_location(log.latitude, log.longitude)
    elif not electricity_board:
        electricity_board = "mseb"  # Default to MSEB
    
    # Get board data
    board_data = INDIAN_ELECTRICITY_BOARDS.get(electricity_board, INDIAN_ELECTRICITY_BOARDS["mseb"])
    
    # Calculate monthly consumption for tiered pricing
    current_month = datetime.now().strftime('%Y-%m')
    monthly_consumption = 0
    if electricity_board == "kseb":
        conn_temp = sqlite3.connect(DB_PATH)
        cursor_temp = conn_temp.cursor()
        cursor_temp.execute("""
            SELECT SUM(energy_kwh) FROM energy_consumption 
            WHERE electricity_board = ? AND strftime('%Y-%m', date) = ?
        """, (electricity_board, current_month))
        result = cursor_temp.fetchone()
        monthly_consumption = result[0] if result[0] else 0
        conn_temp.close()
    
    # Calculate cost using tiered pricing for KSEB
    cost_rupees = calculate_tiered_cost(energy_kwh, electricity_board, monthly_consumption)
    price_per_kwh = cost_rupees / energy_kwh if energy_kwh > 0 else board_data["price_per_kwh"]
    co2_emissions = calculate_energy_co2(energy_kwh, electricity_board)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO energy_consumption 
        (date, power_consumption_watts, duration_hours, energy_kwh, co2_emissions_kg, electricity_board, price_per_kwh, cost_rupees)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (log.date, log.power_consumption_watts, log.duration_hours, energy_kwh, co2_emissions, electricity_board, price_per_kwh, cost_rupees))
    
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return EnergyLogResponse(
        id=log_id,
        date=log.date,
        power_consumption_watts=log.power_consumption_watts,
        duration_hours=log.duration_hours,
        energy_kwh=energy_kwh,
        co2_emissions_kg=co2_emissions,
        electricity_board=electricity_board,
        price_per_kwh=price_per_kwh,
        cost_rupees=cost_rupees,
        created_at=datetime.now().isoformat()
    )

@app.get("/api/commute-logs", response_model=List[CommuteLogResponse])
async def get_commute_logs():
    """Get all commute logs"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, date, transport_mode, distance_km, co2_emissions_kg, created_at
        FROM commute_logs
        ORDER BY date DESC
    """)
    
    logs = []
    for row in cursor.fetchall():
        logs.append(CommuteLogResponse(
            id=row[0],
            date=row[1],
            transport_mode=row[2],
            distance_km=row[3],
            co2_emissions_kg=row[4],
            created_at=row[5]
        ))
    
    conn.close()
    return logs

@app.get("/api/energy-logs", response_model=List[EnergyLogResponse])
async def get_energy_logs():
    """Get all energy consumption logs"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, date, power_consumption_watts, duration_hours, energy_kwh, co2_emissions_kg, 
               electricity_board, price_per_kwh, cost_rupees, created_at
        FROM energy_consumption
        ORDER BY date DESC
    """)
    
    logs = []
    for row in cursor.fetchall():
        logs.append(EnergyLogResponse(
            id=row[0],
            date=row[1],
            power_consumption_watts=row[2],
            duration_hours=row[3],
            energy_kwh=row[4],
            co2_emissions_kg=row[5],
            electricity_board=row[6],
            price_per_kwh=row[7],
            cost_rupees=row[8],
            created_at=row[9]
        ))
    
    conn.close()
    return logs

@app.get("/api/monthly-data", response_model=List[MonthlyData])
async def get_monthly_data():
    """Get monthly aggregated data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Calculate monthly aggregations
    cursor.execute("""
        SELECT 
            strftime('%Y', date) as year,
            strftime('%m', date) as month,
            SUM(co2_emissions_kg) as total_commute_co2,
            SUM(distance_km) as total_distance
        FROM commute_logs
        GROUP BY year, month
        ORDER BY year DESC, month DESC
    """)
    
    commute_data = {}
    for row in cursor.fetchall():
        key = f"{row[0]}-{row[1]}"
        commute_data[key] = {
            'year': int(row[0]),
            'month': int(row[1]),
            'total_commute_co2': row[2] or 0,
            'total_distance': row[3] or 0
        }
    
    cursor.execute("""
        SELECT 
            strftime('%Y', date) as year,
            strftime('%m', date) as month,
            SUM(co2_emissions_kg) as total_energy_co2,
            SUM(energy_kwh) as total_energy
        FROM energy_consumption
        GROUP BY year, month
        ORDER BY year DESC, month DESC
    """)
    
    energy_data = {}
    for row in cursor.fetchall():
        key = f"{row[0]}-{row[1]}"
        energy_data[key] = {
            'total_energy_co2': row[2] or 0,
            'total_energy': row[3] or 0
        }
    
    # Combine data
    monthly_data = []
    all_months = set(commute_data.keys()) | set(energy_data.keys())
    
    for month_key in sorted(all_months, reverse=True):
        commute = commute_data.get(month_key, {})
        energy = energy_data.get(month_key, {})
        
        total_co2 = (commute.get('total_commute_co2', 0) + 
                    energy.get('total_energy_co2', 0))
        
        monthly_data.append(MonthlyData(
            year=commute.get('year', 0),
            month=commute.get('month', 0),
            total_commute_co2=commute.get('total_commute_co2', 0),
            total_energy_co2=energy.get('total_energy_co2', 0),
            total_co2=total_co2,
            commute_distance_km=commute.get('total_distance', 0),
            energy_consumption_kwh=energy.get('total_energy', 0)
        ))
    
    conn.close()
    return monthly_data

@app.get("/api/dashboard-stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total CO2 emissions
    cursor.execute("SELECT SUM(co2_emissions_kg) FROM commute_logs")
    total_commute_co2 = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(co2_emissions_kg) FROM energy_consumption")
    total_energy_co2 = cursor.fetchone()[0] or 0
    
    # Total energy cost
    cursor.execute("SELECT SUM(cost_rupees) FROM energy_consumption")
    total_energy_cost = cursor.fetchone()[0] or 0
    
    # This month's data
    current_month = datetime.now().strftime('%Y-%m')
    cursor.execute("""
        SELECT SUM(co2_emissions_kg) FROM commute_logs 
        WHERE strftime('%Y-%m', date) = ?
    """, (current_month,))
    month_commute_co2 = cursor.fetchone()[0] or 0
    
    cursor.execute("""
        SELECT SUM(co2_emissions_kg) FROM energy_consumption 
        WHERE strftime('%Y-%m', date) = ?
    """, (current_month,))
    month_energy_co2 = cursor.fetchone()[0] or 0
    
    cursor.execute("""
        SELECT SUM(cost_rupees) FROM energy_consumption 
        WHERE strftime('%Y-%m', date) = ?
    """, (current_month,))
    month_energy_cost = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "total_co2_emissions": total_commute_co2 + total_energy_co2,
        "total_commute_co2": total_commute_co2,
        "total_energy_co2": total_energy_co2,
        "total_energy_cost": total_energy_cost,
        "this_month_co2": month_commute_co2 + month_energy_co2,
        "this_month_commute_co2": month_commute_co2,
        "this_month_energy_co2": month_energy_co2,
        "this_month_energy_cost": month_energy_cost
    }

@app.get("/api/electricity-boards", response_model=List[ElectricityBoard])
async def get_electricity_boards():
    """Get all available electricity boards"""
    boards = []
    for board_id, board_data in INDIAN_ELECTRICITY_BOARDS.items():
        boards.append(ElectricityBoard(
            id=board_id,
            name=board_data["name"],
            state=board_data["state"],
            price_per_kwh=board_data["price_per_kwh"],
            emission_factor=board_data["emission_factor"],
            grid_mix=board_data["grid_mix"]
        ))
    return boards

@app.post("/api/location-to-board")
async def get_board_from_location(location: LocationData):
    """Get electricity board based on GPS coordinates"""
    board_id = get_electricity_board_from_location(location.latitude, location.longitude)
    board_data = INDIAN_ELECTRICITY_BOARDS[board_id]
    
    return {
        "board_id": board_id,
        "board_name": board_data["name"],
        "state": board_data["state"],
        "price_per_kwh": board_data["price_per_kwh"],
        "emission_factor": board_data["emission_factor"],
        "grid_mix": board_data["grid_mix"]
    }

@app.get("/api/kseb-slabs")
async def get_kseb_slabs():
    """Get KSEB tiered pricing slabs"""
    return {"slabs": KSEB_SLABS}

@app.get("/api/calculate-tiered-cost")
async def calculate_cost_preview(energy_kwh: float, electricity_board: str, monthly_consumption: float = 0):
    """Calculate cost preview for tiered pricing"""
    cost = calculate_tiered_cost(energy_kwh, electricity_board, monthly_consumption)
    return {
        "energy_kwh": energy_kwh,
        "electricity_board": electricity_board,
        "monthly_consumption": monthly_consumption,
        "cost_rupees": cost,
        "effective_rate": cost / energy_kwh if energy_kwh > 0 else 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
