import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Polygon, useMap, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import axios from 'axios';
import MapClickHandler from './MapClickHandler';
import './RealEnergySitingMap.css';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const RealEnergySitingMap = () => {
  const [mapCenter, setMapCenter] = useState([20.0, 77.0]); // Default to India
  const [mapZoom, setMapZoom] = useState(6);
  const [isDrawing, setIsDrawing] = useState(false);
  const [polygon, setPolygon] = useState([]);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [location, setLocation] = useState({ country: '', state: '', city: '' });
  const [weatherData, setWeatherData] = useState(null);
  const [suitabilityOverlays, setSuitabilityOverlays] = useState({
    solar: [],
    wind: [],
    hydro: []
  });
  const [geminiAnalysis, setGeminiAnalysis] = useState(null);
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [showBottomPanel, setShowBottomPanel] = useState(false);
  const [bestPointsMarkers, setBestPointsMarkers] = useState([]);
  
  const mapRef = useRef(null);
  const API_KEY = "d4dedf23343f89144698209bfdf71833";

  // Location search function
  const searchLocation = async () => {
    if (!location.city || !location.state || !location.country) {
      alert('Please enter country, state, and city');
      return;
    }

    try {
      const query = `${location.city}, ${location.state}, ${location.country}`;
      const response = await axios.get(
        `https://api.openweathermap.org/geo/1.0/direct?q=${encodeURIComponent(query)}&limit=1&appid=${API_KEY}`
      );

      if (response.data && response.data.length > 0) {
        const { lat, lon } = response.data[0];
        setMapCenter([lat, lon]);
        setMapZoom(10);
        
        // Update map view
        if (mapRef.current) {
          mapRef.current.setView([lat, lon], 10);
        }
      } else {
        alert('Location not found. Please check your input.');
      }
    } catch (error) {
      console.error('Error searching location:', error);
      alert('Error searching location. Please try again.');
    }
  };

  // Get weather data for coordinates
  const getWeatherData = async (lat, lon) => {
    try {
      const response = await axios.get(
        `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${API_KEY}&units=metric`
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching weather data:', error);
      return null;
    }
  };

  // Get historical weather data (for more comprehensive analysis)
  const getHistoricalWeatherData = async (lat, lon) => {
    try {
      // Get 5-day forecast
      const forecastResponse = await axios.get(
        `https://api.openweathermap.org/data/2.5/forecast?lat=${lat}&lon=${lon}&appid=${API_KEY}&units=metric`
      );
      return forecastResponse.data;
    } catch (error) {
      console.error('Error fetching historical weather data:', error);
      return null;
    }
  };

  // Calculate solar potential based on weather data
  const calculateSolarPotential = (weatherData) => {
    if (!weatherData) return 0;
    
    const { main, clouds, wind } = weatherData;
    const temperature = main.temp;
    const cloudCover = clouds.all;
    const windSpeed = wind.speed;
    
    // Solar potential calculation
    let potential = 1.0;
    
    // Cloud cover factor (less clouds = better solar)
    potential *= (1 - cloudCover / 100);
    
    // Temperature factor (moderate temperatures are better)
    const tempFactor = temperature > 0 && temperature < 40 ? 1 : 0.8;
    potential *= tempFactor;
    
    // Wind factor (some wind is good for cooling)
    const windFactor = windSpeed > 0 && windSpeed < 10 ? 1 : 0.9;
    potential *= windFactor;
    
    return Math.max(0, Math.min(1, potential));
  };

  // Calculate wind potential based on weather data
  const calculateWindPotential = (weatherData) => {
    if (!weatherData) return 0;
    
    const { wind } = weatherData;
    const windSpeed = wind.speed;
    
    // Wind potential calculation (optimal between 3-12 m/s)
    let potential = 0;
    if (windSpeed >= 3 && windSpeed <= 12) {
      potential = windSpeed / 12;
    } else if (windSpeed > 12) {
      potential = 1 - (windSpeed - 12) / 20; // Decrease for very high winds
    }
    
    return Math.max(0, Math.min(1, potential));
  };

  // Calculate hydro potential based on weather data
  const calculateHydroPotential = (weatherData) => {
    if (!weatherData) return 0;
    
    const { main, rain } = weatherData;
    const humidity = main.humidity;
    const pressure = main.pressure;
    
    // Hydro potential based on humidity and pressure
    let potential = humidity / 100; // Higher humidity is better
    
    // Pressure factor (lower pressure often indicates weather systems)
    const pressureFactor = pressure < 1013 ? 1.2 : 1; // Lower pressure is better
    potential *= pressureFactor;
    
    // Rain factor (if available)
    if (rain && rain['1h']) {
      potential += rain['1h'] / 10; // More rain is better
    }
    
    return Math.max(0, Math.min(1, potential));
  };

  // Generate grid points within polygon
  const generateGridPoints = (polygon) => {
    if (polygon.length < 3) return [];
    
    // Get bounding box
    const lats = polygon.map(p => p[0]);
    const lons = polygon.map(p => p[1]);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLon = Math.min(...lons);
    const maxLon = Math.max(...lons);
    
    // Generate grid points
    const gridPoints = [];
    const step = 0.01; // Approximately 1km spacing
    
    for (let lat = minLat; lat <= maxLat; lat += step) {
      for (let lon = minLon; lon <= maxLon; lon += step) {
        if (isPointInPolygon([lat, lon], polygon)) {
          gridPoints.push([lat, lon]);
        }
      }
    }
    
    return gridPoints;
  };

  // Point in polygon test
  const isPointInPolygon = (point, polygon) => {
    const [x, y] = point;
    let inside = false;
    
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      const [xi, yi] = polygon[i];
      const [xj, yj] = polygon[j];
      
      if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) {
        inside = !inside;
      }
    }
    
    return inside;
  };

  // Send polygon data to backend
  const sendPolygonToBackend = async (polygonPoints, gridPoints) => {
    try {
      const response = await axios.post('http://localhost:8000/api/analyze-polygon', {
        polygon_points: polygonPoints,
        grid_points: gridPoints,
        analysis_type: 'renewable_energy'
      });
      
      console.log('Backend response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error sending data to backend:', error);
      // Don't throw error, just log it so the analysis can continue
      return null;
    }
  };

  // Analyze suitability for all grid points
  const analyzeSuitability = async () => {
    if (polygon.length < 3) {
      alert('Please draw a polygon first');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisResults(null);
    setSuitabilityOverlays([]);

    try {
      const gridPoints = generateGridPoints(polygon);
      
      // Send polygon data to backend first
      console.log('Sending polygon data to backend...');
      const backendResponse = await sendPolygonToBackend(polygon, gridPoints);
      
      // Check if backend response contains structured data
      console.log('Full backend response:', backendResponse);
      
      if (backendResponse && backendResponse.grid_points_data) {
        console.log('Structured data found in backend response:', backendResponse.grid_points_data);
        // Use the structured data from backend instead of generating our own
        const backendAnalysisData = backendResponse.grid_points_data.map(point => ({
          lat: point.coordinates.latitude,
          lon: point.coordinates.longitude,
          solar: point.renewable_energy_potential.solar?.potential || 0,
          wind: point.renewable_energy_potential.wind?.potential || 0,
          hydro: point.renewable_energy_potential.hydro?.potential || 0,
          solar_suitability: point.renewable_energy_potential.solar?.suitability,
          wind_suitability: point.renewable_energy_potential.wind?.suitability,
          hydro_suitability: point.renewable_energy_potential.hydro?.suitability,
          environmental_data: point.environmental_data,
          elevation_data: point.elevation_data,
          analysis_summary: point.analysis_summary,
          renewable_energy_potential: point.renewable_energy_potential
        }));
        
        setAnalysisResults(backendAnalysisData);
        generateStrategicPointsMarkers(backendAnalysisData);
        return; // Exit early since we have backend data
      } else {
        console.log('No structured data found in backend response, using fallback analysis');
      }
      
      const analysisData = [];

      // Process points in batches to avoid API rate limits
      const batchSize = 10;
      for (let i = 0; i < gridPoints.length; i += batchSize) {
        const batch = gridPoints.slice(i, i + batchSize);
        
        const batchPromises = batch.map(async (point) => {
          const [lat, lon] = point;
          const weatherData = await getWeatherData(lat, lon);
          
          if (weatherData) {
            const solarPotential = calculateSolarPotential(weatherData);
            const windPotential = calculateWindPotential(weatherData);
            const hydroPotential = calculateHydroPotential(weatherData);
            
            return {
              lat,
              lon,
              solar: solarPotential,
              wind: windPotential,
              hydro: hydroPotential,
              weather: weatherData
            };
          }
          return null;
        });

        const batchResults = await Promise.all(batchPromises);
        analysisData.push(...batchResults.filter(result => result !== null));
        
        // Small delay to respect API rate limits
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      setAnalysisResults(analysisData);
      
      // Generate strategic points markers (only 10 points with threshold-based coloring)
      generateStrategicPointsMarkers(analysisData);
      
    } catch (error) {
      console.error('Error analyzing suitability:', error);
      alert('Error analyzing suitability. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Generate colored overlays for different energy types
  const generateSuitabilityOverlays = (data) => {
    const overlays = {
      solar: [],
      wind: [],
      hydro: []
    };

    data.forEach(point => {
      const { lat, lon, solar, wind, hydro } = point;
      
      // Solar overlay (green shades)
      if (solar > 0.3) {
        overlays.solar.push({
          lat,
          lon,
          intensity: solar,
          color: getColorForIntensity(solar, 'solar')
        });
      }
      
      // Wind overlay (blue shades)
      if (wind > 0.3) {
        overlays.wind.push({
          lat,
          lon,
          intensity: wind,
          color: getColorForIntensity(wind, 'wind')
        });
      }
      
      // Hydro overlay (purple shades)
      if (hydro > 0.3) {
        overlays.hydro.push({
          lat,
          lon,
          intensity: hydro,
          color: getColorForIntensity(hydro, 'hydro')
        });
      }
    });

    setSuitabilityOverlays(overlays);
  };

  // Get color based on intensity and energy type
  const getColorForIntensity = (intensity, type) => {
    const alpha = Math.max(0.3, intensity);
    
    switch (type) {
      case 'solar':
        return `rgba(34, 197, 94, ${alpha})`; // Green
      case 'wind':
        return `rgba(59, 130, 246, ${alpha})`; // Blue
      case 'hydro':
        return `rgba(147, 51, 234, ${alpha})`; // Purple
      default:
        return `rgba(156, 163, 175, ${alpha})`; // Gray
    }
  };

  // Handle map click for polygon drawing
  const handleMapClick = (e) => {
    if (!isDrawing) return;
    
    const { lat, lng } = e.latlng;
    setPolygon([...polygon, [lat, lng]]);
  };

  // Create mock Gemini analysis for testing
  const createMockGeminiAnalysis = (gridPoints) => {
    return {
      analysis_summary: {
        total_points_analyzed: gridPoints.length,
        suitable_points: Math.floor(gridPoints.length * 0.8),
        rejected_points: Math.floor(gridPoints.length * 0.2),
        overall_recommendations: "This area shows good potential for renewable energy development with multiple energy sources available."
      },
      grid_point_analyses: gridPoints.map((point, index) => ({
        point_id: index + 1,
        coordinates: { latitude: point[0], longitude: point[1] },
        status: Math.random() > 0.2 ? "SUITABLE" : "REJECTED",
        rejection_reason: Math.random() > 0.2 ? null : "Insufficient environmental conditions for renewable energy development",
        recommended_energy_sources: Math.random() > 0.2 ? [
          {
            energy_type: "solar",
            suitability_score: Math.floor(Math.random() * 40) + 60,
            confidence_level: "high",
            technical_reasoning: "High solar radiation and low cloud cover make this location ideal for solar energy generation.",
            implementation_priority: "primary",
            estimated_capacity_potential: "high",
            environmental_considerations: "Minimal environmental impact with proper planning",
            economic_viability: "high"
          },
          {
            energy_type: "wind",
            suitability_score: Math.floor(Math.random() * 30) + 50,
            confidence_level: "medium",
            technical_reasoning: "Moderate wind speeds and consistent patterns suitable for wind energy.",
            implementation_priority: "secondary",
            estimated_capacity_potential: "medium",
            environmental_considerations: "Consider bird migration patterns",
            economic_viability: "medium"
          }
        ] : [],
        overall_assessment: "This location shows strong potential for renewable energy development with multiple viable options.",
        key_environmental_factors: ["High solar radiation", "Moderate wind speeds", "Low environmental sensitivity"],
        risk_factors: ["Weather variability", "Grid connection distance"],
        opportunity_factors: ["Government incentives", "Proximity to infrastructure"]
      })),
      energy_type_summary: {
        solar: {
          total_suitable_points: Math.floor(gridPoints.length * 0.6),
          average_score: 75,
          best_location: 1
        },
        wind: {
          total_suitable_points: Math.floor(gridPoints.length * 0.4),
          average_score: 65,
          best_location: 2
        },
        hydro: {
          total_suitable_points: Math.floor(gridPoints.length * 0.3),
          average_score: 55,
          best_location: 3
        },
        tidal: {
          total_suitable_points: Math.floor(gridPoints.length * 0.2),
          average_score: 45,
          best_location: 4
        },
        geothermal: {
          total_suitable_points: Math.floor(gridPoints.length * 0.1),
          average_score: 35,
          best_location: 5
        }
      },
      strategic_recommendations: {
        primary_energy_focus: "Solar energy development",
        secondary_energy_focus: "Wind energy integration",
        development_phases: ["Phase 1: Solar installation", "Phase 2: Wind integration", "Phase 3: Grid optimization"],
        environmental_impact_assessment: "Low to moderate environmental impact with proper mitigation measures",
        economic_considerations: "Strong economic viability with government incentives and decreasing technology costs"
      }
    };
  };

  // Generate strategic points markers with threshold-based coloring
  const generateStrategicPointsMarkers = (analysisData) => {
    if (!analysisData || analysisData.length === 0) return;
    
    const strategicPoints = [];
    const thresholds = {
      solar: 0.4,    // 40% threshold (moderate+)
      wind: 0.3,     // 30% threshold (small turbines+)
      hydro: 0.3     // 30% threshold (suitable+)
    };
    
    const colors = {
      solar: '#22c55e',    // Green
      wind: '#3b82f6',     // Blue
      hydro: '#9333ea',    // Purple
      multi: '#f59e0b',    // Orange for multi-source
      none: '#6b7280'      // Gray for none
    };
    
    analysisData.forEach((point, index) => {
      const { lat, lon, solar, wind, hydro, environmental_data, elevation_data, analysis_summary, renewable_energy_potential } = point;
      
      // Determine suitable energy types based on thresholds
      const energyScores = { 
        solar: solar || 0, 
        wind: wind || 0, 
        hydro: hydro || 0 
      };
      
      const suitableTypes = [];
      if (energyScores.solar >= thresholds.solar) suitableTypes.push('solar');
      if (energyScores.wind >= thresholds.wind) suitableTypes.push('wind');
      if (energyScores.hydro >= thresholds.hydro) suitableTypes.push('hydro');
      
      // Determine marker type and color
      let energyType, color, bestScore;
      
      if (suitableTypes.length > 1) {
        // Multi-source point
        energyType = 'multi';
        color = colors.multi;
        bestScore = Math.max(...suitableTypes.map(type => energyScores[type]));
      } else if (suitableTypes.length === 1) {
        // Single source point
        energyType = suitableTypes[0];
        color = colors[energyType];
        bestScore = energyScores[energyType];
      } else {
        // No suitable sources
        energyType = 'none';
        color = colors.none;
        bestScore = Math.max(energyScores.solar, energyScores.wind, energyScores.hydro);
      }
      
      strategicPoints.push({
        id: `strategic_${index + 1}`,
        coordinates: { latitude: lat, longitude: lon },
        energyType: energyType,
        color: color,
        score: bestScore,
        allScores: energyScores,
        suitableTypes: suitableTypes,
        environmental_data: environmental_data,
        elevation_data: elevation_data,
        analysis_summary: analysis_summary,
        renewable_energy_potential: renewable_energy_potential,
        isHighPotential: energyType !== 'none'
      });
    });
    
    setBestPointsMarkers(strategicPoints);
  };

  // Handle point click
  const handlePointClick = (point) => {
    setSelectedPoint(point);
    setShowBottomPanel(true);
  };

  // Clear polygon
  const clearPolygon = () => {
    setPolygon([]);
    setAnalysisResults(null);
    setSuitabilityOverlays({
      solar: [],
      wind: [],
      hydro: []
    });
    setGeminiAnalysis(null);
    setSelectedPoint(null);
    setShowBottomPanel(false);
    setBestPointsMarkers([]);
  };

  return (
    <div className="real-energy-siting-container">
      <div className="siting-header">
        <h2>Renewable Energy Siting Analysis</h2>
        <p>Search for a location, draw a polygon, and analyze renewable energy potential</p>
      </div>

      {/* Location Search */}
      <div className="location-search">
        <div className="search-inputs">
          <input
            type="text"
            placeholder="Country"
            value={location.country}
            onChange={(e) => setLocation({...location, country: e.target.value})}
          />
          <input
            type="text"
            placeholder="State/Province"
            value={location.state}
            onChange={(e) => setLocation({...location, state: e.target.value})}
          />
          <input
            type="text"
            placeholder="City"
            value={location.city}
            onChange={(e) => setLocation({...location, city: e.target.value})}
          />
          <button className="btn-primary" onClick={searchLocation}>
            Search Location
          </button>
        </div>
      </div>

      {/* Map Controls */}
      <div className="map-controls">
        <button 
          className={`btn-primary ${isDrawing ? 'active' : ''}`}
          onClick={() => setIsDrawing(!isDrawing)}
          disabled={isAnalyzing}
        >
          {isDrawing ? 'Stop Drawing' : 'Start Drawing'}
        </button>
        <button 
          className="btn-secondary"
          onClick={clearPolygon}
          disabled={isAnalyzing}
        >
          Clear Polygon
        </button>
        <button 
          className="btn-primary"
          onClick={analyzeSuitability}
          disabled={polygon.length < 3 || isAnalyzing}
        >
          {isAnalyzing ? 'Analyzing...' : 'Analyze Suitability'}
        </button>
      </div>

      {/* Analysis Progress */}
      {isAnalyzing && (
        <div className="analysis-progress">
          <div className="progress-bar">
            <div className="progress-fill"></div>
          </div>
          <p>Fetching weather data and analyzing suitability...</p>
        </div>
      )}

      {/* Map */}
      <div className="map-container">
        <MapContainer
          center={mapCenter}
          zoom={mapZoom}
          style={{ height: '500px', width: '100%' }}
          ref={mapRef}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          
          <MapClickHandler 
            isDrawing={isDrawing} 
            onMapClick={handleMapClick} 
          />
          
          {/* Polygon */}
          {polygon.length > 0 && (
            <Polygon
              positions={polygon}
              pathOptions={{
                color: '#2DD4BF',
                weight: 3,
                fillOpacity: 0.2
              }}
            />
          )}
          
          {/* Suitability Overlays */}
          {/* Strategic Points Only - No old suitability overlays */}
          
          {/* Strategic Points Markers */}
          {bestPointsMarkers.map((point) => (
            <Marker
              key={point.id}
              position={[point.coordinates.latitude, point.coordinates.longitude]}
              icon={L.divIcon({
                className: 'strategic-point-marker',
                html: `
                  <div style="
                    background-color: ${point.color}; 
                    width: ${point.isHighPotential ? '16px' : '12px'}; 
                    height: ${point.isHighPotential ? '16px' : '12px'}; 
                    border-radius: 50%; 
                    border: 2px solid white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    color: white;
                    font-size: ${point.isHighPotential ? '10px' : '8px'};
                  ">
                    ${point.isHighPotential ? point.energyType.charAt(0).toUpperCase() : '•'}
                  </div>
                `,
                iconSize: point.isHighPotential ? [16, 16] : [12, 12]
              })}
              eventHandlers={{
                click: () => handlePointClick(point)
              }}
            >
              <Popup>
                <div>
                  <h4>{point.isHighPotential ? `${point.energyType.toUpperCase()} Energy Site` : 'General Site'}</h4>
                  <p>Solar: {(point.allScores.solar * 100).toFixed(1)}%</p>
                  <p>Wind: {(point.allScores.wind * 100).toFixed(1)}%</p>
                  <p>Hydro: {(point.allScores.hydro * 100).toFixed(1)}%</p>
                  <p>Click for detailed analysis</p>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {/* Legend */}
      <div className="suitability-legend">
        <h3>Energy Suitability Legend</h3>
        <div className="legend-items">
          <div className="legend-section">
            <h4>Energy Type Indicators</h4>
            <div className="legend-item">
              <div className="legend-color solar"></div>
              <span>Solar Relevant (Green) - Moderate+ suitability</span>
            </div>
            <div className="legend-item">
              <div className="legend-color wind"></div>
              <span>Wind Relevant (Blue) - Small turbines+ suitability</span>
            </div>
            <div className="legend-item">
              <div className="legend-color hydro"></div>
              <span>Hydro Relevant (Purple) - Lakes/Sea/Ocean only</span>
            </div>
            <div className="legend-item">
              <div className="legend-color multi"></div>
              <span>Multi-Source (Orange) - Multiple energy types suitable</span>
            </div>
            <div className="legend-item">
              <div className="legend-color none"></div>
              <span>None Relevant (Gray) - Below all thresholds</span>
            </div>
          </div>
          
          <div className="legend-section">
            <h4>Instructions</h4>
            <div className="legend-item">
              <div className="legend-dot general"></div>
              <span>Click any point to view detailed environmental parameters</span>
            </div>
            <div className="legend-item">
              <div className="legend-dot general"></div>
              <span>Multi-source points show best adaptabilities on click</span>
            </div>
          </div>
        </div>
      </div>

      {/* Results Summary */}
      {analysisResults && (
        <div className="results-summary">
          <h3>Analysis Results</h3>
          <div className="results-grid">
            <div className="result-card">
              <h4>Solar Energy</h4>
              <p>Points analyzed: {suitabilityOverlays?.solar?.length || 0}</p>
              <p>Average potential: {suitabilityOverlays?.solar?.length > 0 ? 
                (suitabilityOverlays.solar.reduce((sum, p) => sum + p.intensity, 0) / suitabilityOverlays.solar.length * 100).toFixed(1) + '%' : 'N/A'}</p>
            </div>
            <div className="result-card">
              <h4>Wind Energy</h4>
              <p>Points analyzed: {suitabilityOverlays?.wind?.length || 0}</p>
              <p>Average potential: {suitabilityOverlays?.wind?.length > 0 ? 
                (suitabilityOverlays.wind.reduce((sum, p) => sum + p.intensity, 0) / suitabilityOverlays.wind.length * 100).toFixed(1) + '%' : 'N/A'}</p>
            </div>
            <div className="result-card">
              <h4>Hydro Energy</h4>
              <p>Points analyzed: {suitabilityOverlays?.hydro?.length || 0}</p>
              <p>Average potential: {suitabilityOverlays?.hydro?.length > 0 ? 
                (suitabilityOverlays.hydro.reduce((sum, p) => sum + p.intensity, 0) / suitabilityOverlays.hydro.length * 100).toFixed(1) + '%' : 'N/A'}</p>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Panel for Selected Point Details */}
      {showBottomPanel && selectedPoint && (
        <div className="bottom-panel">
          <div className="panel-header">
            <h3>{selectedPoint.energyType.toUpperCase()} Energy Site Analysis</h3>
            <button 
              className="close-panel-btn"
              onClick={() => setShowBottomPanel(false)}
            >
              ×
            </button>
          </div>
          
          <div className="panel-content">
            <div className="panel-section">
              <h4>📍 Location Details</h4>
              <p><strong>Coordinates:</strong> {selectedPoint.coordinates.latitude.toFixed(6)}, {selectedPoint.coordinates.longitude.toFixed(6)}</p>
              <p><strong>Energy Type:</strong> {selectedPoint.energyType.toUpperCase()}</p>
              <p><strong>Overall Score:</strong> {selectedPoint.score}/100</p>
            </div>

            <div className="panel-section">
              <h4>🌍 Environmental Parameters</h4>
              
              {/* Display environmental parameters from structured data */}
              {selectedPoint.environmental_data && (
                <div>
                  <p><strong>Environmental Parameters:</strong></p>
                  <div className="env-params-grid">
                    {/* NASA POWER Data */}
                    {selectedPoint.environmental_data.nasa_power && (
                      <>
                        <div className="env-param">
                          <span className="param-label">Solar Radiation:</span>
                          <span className="param-value">
                            {selectedPoint.environmental_data.nasa_power.solar_radiation ? 
                              `${selectedPoint.environmental_data.nasa_power.solar_radiation.toFixed(2)} kW-hr/m²/day` : 
                              'N/A'
                            }
                          </span>
                        </div>
                        <div className="env-param">
                          <span className="param-label">Wind Speed:</span>
                          <span className="param-value">
                            {selectedPoint.environmental_data.nasa_power.wind_speed ? 
                              `${selectedPoint.environmental_data.nasa_power.wind_speed.toFixed(2)} m/s` : 
                              'N/A'
                            }
                          </span>
                        </div>
                      </>
                    )}
                    
                    {/* Water Body Data */}
                    {selectedPoint.environmental_data.water_body && (
                      <>
                        <div className="env-param">
                          <span className="param-label">Is Water Body:</span>
                          <span className="param-value">
                            {selectedPoint.environmental_data.water_body.is_water ? 'Yes' : 'No'}
                          </span>
                        </div>
                        <div className="env-param">
                          <span className="param-label">Water Feature:</span>
                          <span className="param-value">
                            {selectedPoint.environmental_data.water_body.feature || 'N/A'}
                          </span>
                        </div>
                      </>
                    )}
                    
                    {/* Location Data */}
                    {selectedPoint.environmental_data.location && (
                      <div className="env-param">
                        <span className="param-label">Location:</span>
                        <span className="param-value">
                          {selectedPoint.environmental_data.location.display_name || 'Unknown Location'}
                        </span>
                      </div>
                    )}
                    
                    {/* Elevation Data */}
                    {selectedPoint.elevation_data && (
                      <div className="env-param">
                        <span className="param-label">Elevation:</span>
                        <span className="param-value">
                          {selectedPoint.elevation_data.elevation ? 
                            `${selectedPoint.elevation_data.elevation.toFixed(1)} m` : 
                            'N/A'
                          }
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              {/* Analysis Summary */}
              {selectedPoint.analysis_summary && (
                <div>
                  <p><strong>Analysis Summary:</strong></p>
                  <div className="env-params-grid">
                    <div className="env-param">
                      <span className="param-label">Energy Type:</span>
                      <span className="param-value">
                        {selectedPoint.energyType === 'multi' ? 'Multi-Source' : selectedPoint.energyType.toUpperCase()}
                      </span>
                    </div>
                    <div className="env-param">
                      <span className="param-label">Overall Suitability:</span>
                      <span className="param-value">
                        {selectedPoint.analysis_summary.overall_suitability ? 
                          `${(selectedPoint.analysis_summary.overall_suitability * 100).toFixed(1)}%` : 
                          'N/A'
                        }
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Energy Suitability Details */}
              {selectedPoint.renewable_energy_potential && (
                <div>
                  <p><strong>Energy Suitability Details:</strong></p>
                  <div className="env-params-grid">
                    {/* Solar Details */}
                    {selectedPoint.renewable_energy_potential.solar && (
                      <div className="env-param">
                        <span className="param-label">Solar:</span>
                        <span className="param-value">
                          {selectedPoint.renewable_energy_potential.solar.potential ? 
                            `${(selectedPoint.renewable_energy_potential.solar.potential * 100).toFixed(1)}% (${selectedPoint.renewable_energy_potential.solar.suitability})` : 
                            'N/A'
                          }
                        </span>
                      </div>
                    )}
                    
                    {/* Wind Details */}
                    {selectedPoint.renewable_energy_potential.wind && (
                      <div className="env-param">
                        <span className="param-label">Wind:</span>
                        <span className="param-value">
                          {selectedPoint.renewable_energy_potential.wind.potential ? 
                            `${(selectedPoint.renewable_energy_potential.wind.potential * 100).toFixed(1)}% (${selectedPoint.renewable_energy_potential.wind.suitability})` : 
                            'N/A'
                          }
                        </span>
                      </div>
                    )}
                    
                    {/* Hydro Details */}
                    {selectedPoint.renewable_energy_potential.hydro && (
                      <div className="env-param">
                        <span className="param-label">Hydro:</span>
                        <span className="param-value">
                          {selectedPoint.renewable_energy_potential.hydro.potential ? 
                            `${(selectedPoint.renewable_energy_potential.hydro.potential * 100).toFixed(1)}% (${selectedPoint.renewable_energy_potential.hydro.suitability})` : 
                            'N/A'
                          }
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Multi-Source Best Adaptabilities */}
              {selectedPoint.energyType === 'multi' && selectedPoint.suitableTypes && (
                <div>
                  <p><strong>Best Adaptabilities (Multi-Source Location):</strong></p>
                  <div className="env-params-grid">
                    {selectedPoint.suitableTypes.map((type, index) => {
                      const energyData = selectedPoint.renewable_energy_potential[type];
                      return (
                        <div key={index} className="env-param">
                          <span className="param-label">{type.toUpperCase()}:</span>
                          <span className="param-value">
                            {energyData?.potential ? 
                              `${(energyData.potential * 100).toFixed(1)}% - ${energyData.suitability}` : 
                              'N/A'
                            }
                          </span>
                        </div>
                      );
                    })}
                  </div>
                  <p className="multi-source-note">
                    <em>This location is suitable for multiple energy sources. Consider hybrid energy systems for optimal efficiency.</em>
                  </p>
                </div>
              )}

              {selectedPoint.analysis && selectedPoint.analysis.recommended_energy_sources && (
                <div>
                  <p><strong>Recommended Energy Sources:</strong></p>
                  {selectedPoint.analysis.recommended_energy_sources.map((source, index) => (
                    <div key={index} className="energy-source-detail">
                      <h5>{source.energy_type.toUpperCase()}</h5>
                      <p><strong>Suitability Score:</strong> {source.suitability_score}/100</p>
                      <p><strong>Confidence:</strong> {source.confidence_level}</p>
                      <p><strong>Priority:</strong> {source.implementation_priority}</p>
                      <p><strong>Capacity Potential:</strong> {source.estimated_capacity_potential}</p>
                      <p><strong>Economic Viability:</strong> {source.economic_viability}</p>
                      <p><strong>Technical Reasoning:</strong> {source.technical_reasoning}</p>
                      <p><strong>Environmental Considerations:</strong> {source.environmental_considerations}</p>
                    </div>
                  ))}
                </div>
              )}

              {selectedPoint.analysis && selectedPoint.analysis.risk_factors && (
                <div>
                  <p><strong>Risk Factors:</strong></p>
                  <ul>
                    {selectedPoint.analysis.risk_factors.map((risk, index) => (
                      <li key={index}>{risk}</li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedPoint.analysis && selectedPoint.analysis.opportunity_factors && (
                <div>
                  <p><strong>Opportunity Factors:</strong></p>
                  <ul>
                    {selectedPoint.analysis.opportunity_factors.map((opportunity, index) => (
                      <li key={index}>{opportunity}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {geminiAnalysis && geminiAnalysis.strategic_recommendations && (
              <div className="panel-section">
                <h4>🎯 Strategic Recommendations</h4>
                <p><strong>Primary Energy Focus:</strong> {geminiAnalysis.strategic_recommendations.primary_energy_focus}</p>
                <p><strong>Secondary Energy Focus:</strong> {geminiAnalysis.strategic_recommendations.secondary_energy_focus}</p>
                <p><strong>Development Phases:</strong> {geminiAnalysis.strategic_recommendations.development_phases?.join(', ')}</p>
                <p><strong>Environmental Impact:</strong> {geminiAnalysis.strategic_recommendations.environmental_impact_assessment}</p>
                <p><strong>Economic Considerations:</strong> {geminiAnalysis.strategic_recommendations.economic_considerations}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default RealEnergySitingMap;
