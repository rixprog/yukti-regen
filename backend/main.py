from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, date
import sqlite3
import json
from pathlib import Path
import requests
import csv
import pandas as pd
import google.generativeai as genai
from voice_assistant import transcribe_audio, get_ai_response, text_to_speech_elevenlabs
from fastapi import UploadFile, File, Form
import base64
import os
from image_processor import ImageProcessor

app = FastAPI(title="Carbon Footprint Visualizer API", version="1.0.0")

# Initialize image processor
image_processor = ImageProcessor()

# API configuration for new data sources

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyB_Anepsd_vLywEtUlbTdnZQ30c6oFx6d8"
genai.configure(api_key=GEMINI_API_KEY)

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

class PolygonData(BaseModel):
    polygon_points: List[List[float]]  # List of [lat, lon] coordinates
    grid_points: List[List[float]]     # List of [lat, lon] coordinates within polygon
    analysis_type: str = "renewable_energy"  # Type of analysis requested

class GridPointData(BaseModel):
    point_id: int
    coordinates: Dict[str, float]
    elevation_data: Dict
    environmental_data: Dict
    renewable_energy_potential: Dict
    analysis_summary: Dict

class AnalysisMetadata(BaseModel):
    polygon_points_count: int
    grid_points_count: int
    processed_points: int
    analysis_type: str
    estimated_area_km2: float
    grid_density_per_km2: float
    timestamp: str

class StructuredAnalysisResponse(BaseModel):
    analysis_metadata: AnalysisMetadata
    grid_points_data: List[GridPointData]

# Environmental data fetching functions
def get_elevation_data(latitude: float, longitude: float) -> dict:
    """Get elevation data for given coordinates using Open-Elevation API"""
    try:
        response = requests.get(
            f"https://api.open-elevation.com/api/v1/lookup?locations={latitude},{longitude}",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('results') and len(data['results']) > 0:
                return {
                    "elevation": data['results'][0].get('elevation', 0),
                    "latitude": data['results'][0].get('latitude', latitude),
                    "longitude": data['results'][0].get('longitude', longitude)
                }
    except Exception as e:
        print(f"Error fetching elevation data: {e}")
    
    return {
        "elevation": 0,
        "latitude": latitude,
        "longitude": longitude
    }

def get_nasa_power_data(latitude: float, longitude: float) -> dict:
    """Get solar radiation and wind speed data from NASA POWER API"""
    try:
        url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
        params = {
            "parameters": "ALLSKY_SFC_SW_DWN,WS10M",
            "community": "RE",
            "longitude": longitude,
            "latitude": latitude,
            "start": "2023",
            "end": "2023",
            "format": "JSON"
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            properties = data.get("properties", {})
            parameter = properties.get("parameter", {})
            
            # Extract solar radiation data (average of monthly values)
            solar_data = parameter.get("ALLSKY_SFC_SW_DWN", {})
            wind_data = parameter.get("WS10M", {})
            
            # Calculate averages
            solar_values = [v for v in solar_data.values() if isinstance(v, (int, float))]
            wind_values = [v for v in wind_data.values() if isinstance(v, (int, float))]
            
            avg_solar_radiation = sum(solar_values) / len(solar_values) if solar_values else 0
            avg_wind_speed = sum(wind_values) / len(wind_values) if wind_values else 0
            
            return {
                "solar_radiation": avg_solar_radiation,
                "wind_speed": avg_wind_speed,
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude
                }
            }
    except Exception as e:
        print(f"Error fetching NASA POWER data: {e}")
    
    return {
        "solar_radiation": 0,
        "wind_speed": 0,
        "coordinates": {
            "latitude": latitude,
            "longitude": longitude
        }
    }

def get_water_body_data(latitude: float, longitude: float) -> dict:
    """Get water body information using is-on-water API"""
    try:
        url = f"https://is-on-water.balbona.me/api/v1/get/{latitude}/{longitude}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "is_water": data.get("isWater", False),
                "feature": data.get("feature", "UNKNOWN"),
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude
                }
            }
    except Exception as e:
        print(f"Error fetching water body data: {e}")
    
    return {
        "is_water": False,
        "feature": "UNKNOWN",
        "coordinates": {
            "latitude": latitude,
            "longitude": longitude
        }
    }

def get_location_data(latitude: float, longitude: float) -> dict:
    """Get location information using Nominatim reverse geocoding"""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "format": "json",
            "lat": latitude,
            "lon": longitude,
            "zoom": 10
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "display_name": data.get("display_name", "Unknown Location"),
                "address": data.get("address", {}),
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude
                }
            }
    except Exception as e:
        print(f"Error fetching location data: {e}")
    
    return {
        "display_name": "Unknown Location",
        "address": {},
        "coordinates": {
            "latitude": latitude,
            "longitude": longitude
        }
    }

def get_environmental_data(latitude: float, longitude: float) -> dict:
    """Get environmental data from multiple APIs"""
    try:
        # Get data from all three APIs
        nasa_data = get_nasa_power_data(latitude, longitude)
        water_data = get_water_body_data(latitude, longitude)
        location_data = get_location_data(latitude, longitude)
        
        return {
            "nasa_power": nasa_data,
            "water_body": water_data,
            "location": location_data,
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude
            }
        }
    except Exception as e:
        print(f"Error fetching environmental data for {latitude}, {longitude}: {e}")
        return None

def select_strategic_grid_points(grid_points: list, num_points: int = 10) -> list:
    """Select strategic grid points that provide comprehensive coverage of the polygon"""
    if len(grid_points) <= num_points:
        return grid_points
    
    # Calculate polygon bounds
    lats = [point[0] for point in grid_points]
    lons = [point[1] for point in grid_points]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    
    # Create a grid of regions within the polygon
    lat_step = (max_lat - min_lat) / 3  # 3x3 grid
    lon_step = (max_lon - min_lon) / 3
    
    selected_points = []
    regions = {}
    
    # Group points by regions
    for point in grid_points:
        lat, lon = point[0], point[1]
        region_lat = int((lat - min_lat) / lat_step)
        region_lon = int((lon - min_lon) / lon_step)
        region_key = (region_lat, region_lon)
        
        if region_key not in regions:
            regions[region_key] = []
        regions[region_key].append(point)
    
    # Select one point from each region, prioritizing center points
    for region_key, points in regions.items():
        if points:
            # Calculate center of region
            center_lat = min_lat + (region_key[0] + 0.5) * lat_step
            center_lon = min_lon + (region_key[1] + 0.5) * lon_step
            
            # Find point closest to center
            best_point = min(points, key=lambda p: 
                ((p[0] - center_lat) ** 2 + (p[1] - center_lon) ** 2) ** 0.5)
            selected_points.append(best_point)
    
    # If we need more points, add the remaining highest potential points
    if len(selected_points) < num_points:
        remaining_points = [p for p in grid_points if p not in selected_points]
        # Sort by distance from center of polygon
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        remaining_points.sort(key=lambda p: 
            ((p[0] - center_lat) ** 2 + (p[1] - center_lon) ** 2) ** 0.5)
        
        selected_points.extend(remaining_points[:num_points - len(selected_points)])
    
    return selected_points[:num_points]

def calculate_renewable_energy_potential(environmental_data: dict, elevation_data: dict, water_body_proximity: dict = None) -> dict:
    """Calculate renewable energy potential based on environmental and elevation data using proper thresholds"""
    if not environmental_data or not elevation_data:
        return {"solar": None, "wind": None, "hydro": None, "geothermal": None}
    
    nasa_data = environmental_data.get("nasa_power", {})
    water_data = environmental_data.get("water_body", {})
    elevation = elevation_data.get("elevation", None)
    
    # Solar potential calculation using NASA POWER data with proper thresholds
    solar_radiation = nasa_data.get("solar_radiation", None)
    
    if solar_radiation is None or solar_radiation <= 0:
        solar_potential = None
        solar_suitability = "poor"
    else:
        # Solar thresholds based on kWh/m²/day
        if solar_radiation < 3:
            solar_potential = 0.1  # Poor
            solar_suitability = "poor"
        elif 3 <= solar_radiation < 4.5:
            solar_potential = 0.4  # Moderate
            solar_suitability = "moderate"
        elif 4.5 <= solar_radiation < 5.5:
            solar_potential = 0.7  # Good
            solar_suitability = "good"
        else:  # >= 5.5
            solar_potential = 1.0  # Excellent
            solar_suitability = "excellent"
    
    # Wind potential calculation using NASA POWER data with proper thresholds
    wind_speed = nasa_data.get("wind_speed", None)
    
    if wind_speed is None or wind_speed <= 0:
        wind_potential = None
        wind_suitability = "not_usable"
    else:
        # Wind thresholds based on m/s
        if wind_speed < 3:
            wind_potential = 0.0  # Not usable
            wind_suitability = "not_usable"
        elif 3 <= wind_speed < 5:
            wind_potential = 0.3  # Only suitable for very small turbines
            wind_suitability = "small_turbines"
        elif 5 <= wind_speed < 7:
            wind_potential = 0.6  # Good for most onshore turbines
            wind_suitability = "good"
        elif 7 <= wind_speed < 9:
            wind_potential = 0.9  # Excellent wind farm potential
            wind_suitability = "excellent"
        else:  # >= 9
            wind_potential = 0.8  # Very high but may have limitations
            wind_suitability = "very_high"
    
    # Hydro potential calculation - ONLY for lakes, sea, ocean (not smaller ponds)
    is_water = water_data.get("is_water", False)
    water_feature = water_data.get("feature", None)
    
    if not is_water:
        hydro_potential = 0.0
        hydro_suitability = "not_water"
    else:
        # Only consider major water bodies for hydro potential
        if water_feature in ["LAKE", "SEA", "OCEAN"]:
            if elevation is not None and elevation > 100:  # Higher elevation = better hydro potential
                hydro_potential = min(1.0, elevation / 1000)
                hydro_suitability = "suitable"
            else:
                hydro_potential = 0.5  # Water body but low elevation
                hydro_suitability = "moderate"
        else:
            hydro_potential = 0.0  # Smaller ponds, rivers not suitable for large hydro
            hydro_suitability = "not_suitable"
    
    # Geothermal potential (based on elevation only)
    if elevation is None:
        geothermal_potential = None
        geothermal_suitability = "unknown"
    else:
        if elevation > 2000:
            geothermal_potential = 0.8
            geothermal_suitability = "high"
        elif elevation > 1000:
            geothermal_potential = 0.5
            geothermal_suitability = "moderate"
        else:
            geothermal_potential = 0.2
            geothermal_suitability = "low"
    
    return {
        "solar": {
            "potential": round(solar_potential, 3) if solar_potential is not None else None,
            "suitability": solar_suitability,
            "raw_value": solar_radiation
        },
        "wind": {
            "potential": round(wind_potential, 3) if wind_potential is not None else None,
            "suitability": wind_suitability,
            "raw_value": wind_speed
        },
        "hydro": {
            "potential": round(hydro_potential, 3) if hydro_potential is not None else None,
            "suitability": hydro_suitability,
            "raw_value": water_feature
        },
        "geothermal": {
            "potential": round(geothermal_potential, 3) if geothermal_potential is not None else None,
            "suitability": geothermal_suitability,
            "raw_value": elevation
        }
    }

def _get_best_energy_type(energy_potential: dict) -> str:
    """Get the best energy type from potential values"""
    if not energy_potential:
        return "none"
    
    # Filter out None values and find the maximum potential
    valid_potentials = {}
    for energy_type, data in energy_potential.items():
        if isinstance(data, dict) and data.get("potential") is not None and data.get("potential", 0) > 0:
            valid_potentials[energy_type] = data["potential"]
    
    if not valid_potentials:
        return "none"
    
    return max(valid_potentials.items(), key=lambda x: x[1])[0]

def _get_overall_suitability(energy_potential: dict) -> float:
    """Get the overall suitability score"""
    if not energy_potential:
        return 0.0
    
    # Filter out None values and find the maximum potential
    valid_potentials = []
    for energy_type, data in energy_potential.items():
        if isinstance(data, dict) and data.get("potential") is not None and data.get("potential", 0) > 0:
            valid_potentials.append(data["potential"])
    
    if not valid_potentials:
        return 0.0
    
    return max(valid_potentials)

def _get_suitable_energy_types(energy_potential: dict) -> list:
    """Get all energy types that are suitable (potential > 0.3)"""
    suitable_types = []
    for energy_type, data in energy_potential.items():
        if isinstance(data, dict) and data.get("potential") is not None and data.get("potential", 0) >= 0.3:
            suitable_types.append(energy_type)
    return suitable_types

def analyze_with_gemini(grid_points_data: list) -> dict:
    """Analyze grid points using Gemini 2.0 Flash for renewable energy suitability"""
    try:
        # Prepare data for Gemini
        analysis_prompt = f"""
You are an expert renewable energy consultant analyzing environmental data for optimal energy plant placement. 

Analyze the following {len(grid_points_data)} grid points and determine their suitability for different renewable energy sources (Solar, Wind, Hydro, Tidal, Geothermal).

IMPORTANT RULES:
1. If a grid point is not suitable for ANY renewable energy source, mark it as "REJECTED" with reason
2. For suitable points, identify ALL possible renewable energy sources (not just the best one)
3. Provide confidence scores (0-100) for each energy type
4. Give specific technical reasoning for each decision
5. Consider environmental constraints, weather patterns, elevation, and geographical factors

SPECIAL FOCUS ON HYDRO POWER:
- Prioritize hydro power recommendations for points closer to water bodies (lakes, rivers, dams)
- Consider elevation differences for hydroelectric potential
- Analyze precipitation patterns and water flow potential
- Look for points with higher elevation that could benefit from gravity-fed systems
- Consider proximity to existing water infrastructure

ENVIRONMENTAL PARAMETERS AVAILABLE:
- Solar: shortwave_radiation, direct_radiation, global_tilted_irradiance, cloud_cover, uv_index, temperature
- Wind: wind_speed_10m, wind_speed_80m, wind_speed_120m, wind_direction_10m
- Hydro: precipitation, rain, relative_humidity_2m, elevation, proximity to water bodies
- Tidal: proximity to coast, elevation, precipitation patterns
- Geothermal: elevation, temperature gradients, geological factors

GEOGRAPHICAL CONTEXT:
- This analysis is for Kerala, India (coordinates around 10.7°N, 76.4°E)
- Kerala has numerous rivers, backwaters, and water bodies
- Consider the Western Ghats mountain range for elevation-based hydro potential
- Look for points with significant elevation changes for hydroelectric potential

GRID POINTS DATA:
{json.dumps(grid_points_data, indent=2, default=str)}

Please provide your analysis in the following JSON structure:
{{
    "analysis_summary": {{
        "total_points_analyzed": {len(grid_points_data)},
        "suitable_points": 0,
        "rejected_points": 0,
        "overall_recommendations": "string"
    }},
    "grid_point_analyses": [
        {{
            "point_id": 1,
            "coordinates": {{"latitude": 0.0, "longitude": 0.0}},
            "status": "SUITABLE" or "REJECTED",
            "rejection_reason": "string if rejected",
            "recommended_energy_sources": [
                {{
                    "energy_type": "solar/wind/hydro/tidal/geothermal",
                    "suitability_score": 85,
                    "confidence_level": "high/medium/low",
                    "technical_reasoning": "detailed explanation",
                    "implementation_priority": "primary/secondary/tertiary",
                    "estimated_capacity_potential": "high/medium/low",
                    "environmental_considerations": "string",
                    "economic_viability": "high/medium/low"
                }}
            ],
            "overall_assessment": "comprehensive summary",
            "key_environmental_factors": ["factor1", "factor2", "factor3"],
            "risk_factors": ["risk1", "risk2"],
            "opportunity_factors": ["opp1", "opp2"]
        }}
    ],
    "energy_type_summary": {{
        "solar": {{"total_suitable_points": 0, "average_score": 0, "best_location": "point_id"}},
        "wind": {{"total_suitable_points": 0, "average_score": 0, "best_location": "point_id"}},
        "hydro": {{"total_suitable_points": 0, "average_score": 0, "best_location": "point_id"}},
        "tidal": {{"total_suitable_points": 0, "average_score": 0, "best_location": "point_id"}},
        "geothermal": {{"total_suitable_points": 0, "average_score": 0, "best_location": "point_id"}}
    }},
    "strategic_recommendations": {{
        "primary_energy_focus": "string",
        "secondary_energy_focus": "string",
        "development_phases": ["phase1", "phase2", "phase3"],
        "environmental_impact_assessment": "string",
        "economic_considerations": "string"
    }}
}}

Be thorough, technical, and practical in your analysis. Consider real-world implementation challenges and opportunities.
"""

        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        print("🤖 Sending data to Gemini 2.0 Flash for analysis...")
        print("=" * 60)
        
        # Generate response
        response = model.generate_content(analysis_prompt)
        
        print("✅ Gemini analysis completed!")
        print("=" * 60)
        print(f"Raw Gemini response (first 500 chars): {response.text[:500]}...")
        print("=" * 60)
        
        # Parse JSON response - handle markdown code blocks
        try:
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith("```"):
                response_text = response_text[3:]   # Remove ```
            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove trailing ```
            
            response_text = response_text.strip()
            
            gemini_analysis = json.loads(response_text)
            return {
                "status": "success",
                "gemini_analysis": gemini_analysis,
                "raw_response": response.text
            }
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing Gemini JSON response: {e}")
            print(f"Cleaned response text: {response_text[:500]}...")
            return {
                "status": "error",
                "message": "Failed to parse Gemini response as JSON",
                "raw_response": response.text
            }
            
    except Exception as e:
        print(f"❌ Error in Gemini analysis: {e}")
        return {
            "status": "error",
            "message": f"Gemini analysis failed: {str(e)}",
            "raw_response": None
        }

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

@app.post("/api/analyze-polygon", response_model=StructuredAnalysisResponse)
async def analyze_polygon_data(polygon_data: PolygonData):
    """Receive polygon data from frontend and process environmental data for each grid point"""
    print("=" * 80)
    print("🌍 RENEWABLE ENERGY SITING ANALYSIS - COMPREHENSIVE DATA PROCESSING")
    print("=" * 80)
    
    # Print polygon information
    print(f"📍 Polygon Points: {len(polygon_data.polygon_points)} coordinates")
    print("   Polygon coordinates:")
    for i, point in enumerate(polygon_data.polygon_points):
        print(f"   Point {i+1}: [{point[0]:.6f}, {point[1]:.6f}]")
    
    print(f"\n🗺️  Grid Points: {len(polygon_data.grid_points)} points within polygon")
    
    # Calculate polygon area (approximate)
    area_km2 = 0
    if len(polygon_data.polygon_points) >= 3:
        # Simple shoelace formula for polygon area
        area = 0
        n = len(polygon_data.polygon_points)
        for i in range(n):
            j = (i + 1) % n
            area += polygon_data.polygon_points[i][1] * polygon_data.polygon_points[j][0]
            area -= polygon_data.polygon_points[j][1] * polygon_data.polygon_points[i][0]
        area = abs(area) / 2
        
        # Convert to approximate square kilometers (rough conversion)
        area_km2 = area * 111 * 111  # Very rough conversion
        print(f"\n📏 Estimated Area: {area_km2:.2f} km²")
    
    # Select 10 strategic grid points that cover the entire polygon
    grid_points_to_process = select_strategic_grid_points(polygon_data.grid_points, 10)
    print(f"\n🔬 Processing {len(grid_points_to_process)} strategic grid points for environmental analysis...")
    print("📍 Selected strategic points for comprehensive polygon coverage:")
    for i, point in enumerate(grid_points_to_process):
        print(f"   Point {i+1}: [{point[0]:.6f}, {point[1]:.6f}]")
    
    structured_data = {
        "analysis_metadata": {
            "polygon_points_count": len(polygon_data.polygon_points),
            "grid_points_count": len(polygon_data.grid_points),
            "processed_points": len(grid_points_to_process),
            "analysis_type": polygon_data.analysis_type,
            "estimated_area_km2": area_km2,
            "grid_density_per_km2": len(polygon_data.grid_points) / area_km2 if area_km2 > 0 else 0,
            "timestamp": datetime.now().isoformat()
        },
        "grid_points_data": []
    }
    
    for i, point in enumerate(grid_points_to_process):
        latitude, longitude = point[0], point[1]
        print(f"\n{'='*60}")
        print(f"📍 PROCESSING GRID POINT {i+1}/{len(grid_points_to_process)}")
        print(f"   Coordinates: [{latitude:.6f}, {longitude:.6f}]")
        print(f"{'='*60}")
        
        # Fetch elevation data
        print("   🏔️  Fetching elevation data...")
        elevation_data = get_elevation_data(latitude, longitude)
        print(f"   Elevation: {elevation_data['elevation']:.2f} m")
        
        # Fetch environmental data
        print("   🌤️  Fetching environmental data...")
        environmental_data = get_environmental_data(latitude, longitude)
        
        if environmental_data:
            print("   ✅ Environmental data fetched successfully")
            nasa_data = environmental_data.get("nasa_power", {})
            water_data = environmental_data.get("water_body", {})
            location_data = environmental_data.get("location", {})
            print(f"   Solar Radiation: {nasa_data.get('solar_radiation', 'N/A')} kW-hr/m²/day")
            print(f"   Wind Speed: {nasa_data.get('wind_speed', 'N/A')} m/s")
            print(f"   Is Water Body: {water_data.get('is_water', 'N/A')}")
            print(f"   Water Feature: {water_data.get('feature', 'N/A')}")
            print(f"   Location: {location_data.get('display_name', 'N/A')}")
        else:
            print("   ❌ Failed to fetch environmental data")
        
        # Use only real API data - no simulated values
        water_body_proximity = None
        
        # Calculate renewable energy potential
        print("   ⚡ Calculating renewable energy potential...")
        energy_potential = calculate_renewable_energy_potential(environmental_data, elevation_data, water_body_proximity)
        print(f"   Solar Potential: {energy_potential['solar']['potential']:.3f} ({energy_potential['solar']['suitability']})")
        print(f"   Wind Potential: {energy_potential['wind']['potential']:.3f} ({energy_potential['wind']['suitability']})")
        print(f"   Hydro Potential: {energy_potential['hydro']['potential']:.3f} ({energy_potential['hydro']['suitability']})")
        print(f"   Geothermal Potential: {energy_potential['geothermal']['potential']:.3f} ({energy_potential['geothermal']['suitability']})")
        print(f"   Water Body: {water_data.get('is_water', 'N/A')} - {water_data.get('feature', 'N/A')}")
        
        # Create structured data for this grid point
        suitable_energy_types = _get_suitable_energy_types(energy_potential)
        grid_point_data = {
            "point_id": i + 1,
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude
            },
            "elevation_data": elevation_data,
            "environmental_data": environmental_data,
            "renewable_energy_potential": energy_potential,
            "analysis_summary": {
                "best_energy_type": _get_best_energy_type(energy_potential),
                "overall_suitability": _get_overall_suitability(energy_potential),
                "suitable_energy_types": suitable_energy_types,
                "is_multi_source": len(suitable_energy_types) > 1,
                "environmental_conditions": {
                    "solar_radiation": nasa_data.get('solar_radiation'),
                    "wind_speed": nasa_data.get('wind_speed'),
                    "is_water_body": water_data.get('is_water'),
                    "water_feature": water_data.get('feature'),
                    "location_name": location_data.get('display_name'),
                    "elevation": elevation_data.get('elevation')
                }
            }
        }
        
        structured_data["grid_points_data"].append(grid_point_data)
    
    # Print comprehensive summary
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE ANALYSIS SUMMARY")
    print(f"{'='*80}")
    
    # Calculate overall statistics
    all_energy_potentials = [point["renewable_energy_potential"] for point in structured_data["grid_points_data"]]
    
    if all_energy_potentials:
        # Calculate averages using the new data structure
        solar_potentials = [p["solar"]["potential"] for p in all_energy_potentials if p["solar"]["potential"] is not None]
        wind_potentials = [p["wind"]["potential"] for p in all_energy_potentials if p["wind"]["potential"] is not None]
        hydro_potentials = [p["hydro"]["potential"] for p in all_energy_potentials if p["hydro"]["potential"] is not None]
        geothermal_potentials = [p["geothermal"]["potential"] for p in all_energy_potentials if p["geothermal"]["potential"] is not None]
        
        avg_solar = sum(solar_potentials) / len(solar_potentials) if solar_potentials else 0
        avg_wind = sum(wind_potentials) / len(wind_potentials) if wind_potentials else 0
        avg_hydro = sum(hydro_potentials) / len(hydro_potentials) if hydro_potentials else 0
        avg_geothermal = sum(geothermal_potentials) / len(geothermal_potentials) if geothermal_potentials else 0
        
        print(f"🌞 Average Solar Potential: {avg_solar:.3f}")
        print(f"💨 Average Wind Potential: {avg_wind:.3f}")
        print(f"💧 Average Hydro Potential: {avg_hydro:.3f}")
        print(f"🌋 Average Geothermal Potential: {avg_geothermal:.3f}")
        
        # Find best locations for each energy type
        best_solar = max(structured_data["grid_points_data"], 
                        key=lambda x: x["renewable_energy_potential"]["solar"]["potential"] or 0)
        best_wind = max(structured_data["grid_points_data"], 
                       key=lambda x: x["renewable_energy_potential"]["wind"]["potential"] or 0)
        best_hydro = max(structured_data["grid_points_data"], 
                        key=lambda x: x["renewable_energy_potential"]["hydro"]["potential"] or 0)
        
        print(f"\n🏆 BEST LOCATIONS:")
        print(f"   Solar: Point {best_solar['point_id']} - {best_solar['renewable_energy_potential']['solar']['potential']:.3f} potential ({best_solar['renewable_energy_potential']['solar']['suitability']})")
        print(f"   Wind: Point {best_wind['point_id']} - {best_wind['renewable_energy_potential']['wind']['potential']:.3f} potential ({best_wind['renewable_energy_potential']['wind']['suitability']})")
        print(f"   Hydro: Point {best_hydro['point_id']} - {best_hydro['renewable_energy_potential']['hydro']['potential']:.3f} potential ({best_hydro['renewable_energy_potential']['hydro']['suitability']})")
    
    print(f"\n{'='*80}")
    print("✅ ENVIRONMENTAL DATA COLLECTION COMPLETE")
    print(f"{'='*80}")
    
    # Send data to Gemini for intelligent analysis
    print(f"\n🤖 SENDING DATA TO GEMINI 2.0 FLASH FOR INTELLIGENT ANALYSIS...")
    print("=" * 80)
    
    # Print the structured data in a more readable format
    print("📊 STRUCTURED DATA OUTPUT:")
    print(json.dumps(structured_data, indent=2, default=str))
    
    # Return the structured data as a proper response model
    return StructuredAnalysisResponse(
        analysis_metadata=AnalysisMetadata(**structured_data["analysis_metadata"]),
        grid_points_data=[GridPointData(**point) for point in structured_data["grid_points_data"]]
    )

# Voice Assistant Endpoints
@app.post("/api/voice/transcribe")
async def transcribe_voice(audio_file: UploadFile = File(...)):
    """Transcribe uploaded audio file to text"""
    try:
        # Read the audio file content
        audio_content = await audio_file.read()
        
        # Transcribe using voice assistant
        transcription = transcribe_audio(audio_content, audio_file.filename)
        
        return {
            "status": "success",
            "transcription": transcription,
            "filename": audio_file.filename
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Transcription failed: {str(e)}"
        }

@app.post("/api/voice/chat")
async def voice_chat(request: dict):
    """Process text input and return AI response"""
    try:
        text = request.get("text", "")
        if not text:
            return {
                "status": "error",
                "message": "No text provided"
            }
        
        # Get AI response
        ai_response = get_ai_response(text)
        
        return {
            "status": "success",
            "response": ai_response
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"AI response failed: {str(e)}"
        }

@app.post("/api/voice/synthesize")
async def synthesize_speech(request: dict):
    """Convert text to speech and return audio"""
    try:
        text = request.get("text", "")
        if not text:
            return {
                "status": "error",
                "message": "No text provided"
            }
        
        # Convert text to speech
        audio_bytes = text_to_speech_elevenlabs(text)
        
        # Encode audio as base64 for JSON response
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return {
            "status": "success",
            "audio": audio_base64,
            "format": "mp3"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Speech synthesis failed: {str(e)}"
        }

@app.post("/api/voice/process")
async def process_voice_interaction(audio_file: UploadFile = File(...)):
    """Complete voice interaction: transcribe -> AI response -> synthesize"""
    try:
        # Step 1: Transcribe audio
        audio_content = await audio_file.read()
        transcription = transcribe_audio(audio_content, audio_file.filename)
        
        # Step 2: Get AI response
        ai_response = get_ai_response(transcription)
        
        # Step 3: Convert response to speech
        audio_bytes = text_to_speech_elevenlabs(ai_response)
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return {
            "status": "success",
            "transcription": transcription,
            "ai_response": ai_response,
            "audio": audio_base64,
            "format": "mp3"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Voice processing failed: {str(e)}"
        }

# Image Processing Endpoints
@app.post("/api/images/upload")
async def upload_image(image_file: UploadFile = File(...)):
    """Upload an image file"""
    try:
        # Validate file type
        if not image_file.content_type.startswith('image/'):
            return {
                "status": "error",
                "message": "File must be an image"
            }
        
        # Save the uploaded image
        file_path = image_processor.save_uploaded_image(image_file.file, image_file.filename)
        
        return {
            "status": "success",
            "message": "Image uploaded successfully",
            "filename": os.path.basename(file_path),
            "url": f"/api/images/uploaded/{os.path.basename(file_path)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Image upload failed: {str(e)}"
        }

@app.post("/api/images/process")
async def process_image_with_ai(image_file: UploadFile = File(...), prompt: str = Form(...)):
    """Process uploaded image with AI"""
    try:
        if not prompt:
            return {
                "status": "error",
                "message": "Prompt is required"
            }
        
        # Save the uploaded image
        file_path = image_processor.save_uploaded_image(image_file.file, image_file.filename)
        
        # Process with AI
        result = image_processor.process_image_with_ai(file_path, prompt)
        
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Image processing failed: {str(e)}"
        }

@app.post("/api/images/generate")
async def generate_image_from_prompt(request: dict):
    """Generate image from text prompt"""
    try:
        prompt = request.get("prompt", "")
        if not prompt:
            return {
                "status": "error",
                "message": "Prompt is required"
            }
        
        result = image_processor.generate_image_from_prompt(prompt)
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Image generation failed: {str(e)}"
        }

@app.get("/api/images/list/{image_type}")
async def list_images(image_type: str):
    """List images of a specific type"""
    try:
        valid_types = ["uploaded", "generated", "before", "after"]
        if image_type not in valid_types:
            return {
                "status": "error",
                "message": f"Invalid image type. Must be one of: {valid_types}"
            }
        
        images = image_processor.list_images(image_type)
        return {
            "status": "success",
            "images": images,
            "count": len(images)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to list images: {str(e)}"
        }

@app.get("/api/images/test")
async def test_image_serving():
    """Test endpoint to verify image serving is working"""
    try:
        # Check if directories exist
        directories = {
            "uploaded_images": "uploaded_images",
            "generated_images": "generated_images", 
            "before_images": "before_images",
            "after_images": "after_images"
        }
        
        results = {}
        for name, path in directories.items():
            if os.path.exists(path):
                files = os.listdir(path)
                results[name] = {
                    "exists": True,
                    "file_count": len(files),
                    "files": files[:5]  # First 5 files
                }
            else:
                results[name] = {
                    "exists": False,
                    "file_count": 0,
                    "files": []
                }
        
        return {
            "status": "success",
            "directories": results,
            "message": "Image serving test completed"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Test failed: {str(e)}"
        }

@app.get("/api/images/edits/count")
async def get_edit_count():
    """Get the total count of edit images"""
    try:
        count = image_processor.get_edit_count()
        return {
            "status": "success",
            "edit_count": count
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get edit count: {str(e)}"
        }

@app.get("/api/images/edits/all")
async def get_all_edits():
    """Get all edit images with their numbers"""
    try:
        images = image_processor.list_images("after")
        return {
            "status": "success",
            "images": images,
            "count": len(images),
            "edit_numbers": [img.get("edit_number") for img in images if img.get("edit_number")]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get edit images: {str(e)}"
        }

# Mount static files for serving images (must be after all routes)
app.mount("/api/images/uploaded", StaticFiles(directory="uploaded_images"), name="uploaded_images")
app.mount("/api/images/generated", StaticFiles(directory="generated_images"), name="generated_images")
app.mount("/api/images/before", StaticFiles(directory="before_images"), name="before_images")
app.mount("/api/images/after", StaticFiles(directory="after_images"), name="after_images")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
