import React, { useState, useRef, useEffect } from 'react';
import './EnergySitingMap.css';

const EnergySitingMap = () => {
  const [isDrawing, setIsDrawing] = useState(false);
  const [polygon, setPolygon] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [selectedEnergyType, setSelectedEnergyType] = useState('solar');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const mapRef = useRef(null);
  const canvasRef = useRef(null);

  // Mock environmental data - in real implementation, this would come from APIs
  const environmentalData = {
    elevation: {
      min: 0,
      max: 2000,
      data: generateMockElevationData()
    },
    solarRadiation: {
      min: 0,
      max: 6.5,
      data: generateMockSolarData()
    },
    windSpeed: {
      min: 0,
      max: 15,
      data: generateMockWindData()
    },
    rainfall: {
      min: 0,
      max: 2000,
      data: generateMockRainfallData()
    },
    landCover: {
      types: ['forest', 'grassland', 'urban', 'water', 'agricultural'],
      data: generateMockLandCoverData()
    }
  };

  // Generate mock data for demonstration
  function generateMockElevationData() {
    const data = [];
    for (let i = 0; i < 100; i++) {
      for (let j = 0; j < 100; j++) {
        data.push({
          x: i,
          y: j,
          value: Math.random() * 2000 + Math.sin(i * 0.1) * 500
        });
      }
    }
    return data;
  }

  function generateMockSolarData() {
    const data = [];
    for (let i = 0; i < 100; i++) {
      for (let j = 0; j < 100; j++) {
        data.push({
          x: i,
          y: j,
          value: 3 + Math.random() * 3 + Math.sin(i * 0.05) * 0.5
        });
      }
    }
    return data;
  }

  function generateMockWindData() {
    const data = [];
    for (let i = 0; i < 100; i++) {
      for (let j = 0; j < 100; j++) {
        data.push({
          x: i,
          y: j,
          value: 5 + Math.random() * 10 + Math.cos(j * 0.1) * 2
        });
      }
    }
    return data;
  }

  function generateMockRainfallData() {
    const data = [];
    for (let i = 0; i < 100; i++) {
      for (let j = 0; j < 100; j++) {
        data.push({
          x: i,
          y: j,
          value: 500 + Math.random() * 1500 + Math.sin(i * 0.08) * 300
        });
      }
    }
    return data;
  }

  function generateMockLandCoverData() {
    const data = [];
    const types = ['forest', 'grassland', 'urban', 'water', 'agricultural'];
    for (let i = 0; i < 100; i++) {
      for (let j = 0; j < 100; j++) {
        data.push({
          x: i,
          y: j,
          value: types[Math.floor(Math.random() * types.length)]
        });
      }
    }
    return data;
  }

  // Calculate slope from elevation data
  const calculateSlope = (elevationData, x, y) => {
    const neighbors = [
      { dx: -1, dy: -1 }, { dx: 0, dy: -1 }, { dx: 1, dy: -1 },
      { dx: -1, dy: 0 }, { dx: 1, dy: 0 },
      { dx: -1, dy: 1 }, { dx: 0, dy: 1 }, { dx: 1, dy: 1 }
    ];

    let sumSlope = 0;
    let count = 0;

    neighbors.forEach(neighbor => {
      const nx = x + neighbor.dx;
      const ny = y + neighbor.dy;
      
      if (nx >= 0 && nx < 100 && ny >= 0 && ny < 100) {
        const currentElev = elevationData.find(d => d.x === x && d.y === y)?.value || 0;
        const neighborElev = elevationData.find(d => d.x === nx && d.y === ny)?.value || 0;
        const slope = Math.abs(neighborElev - currentElev) / Math.sqrt(neighbor.dx**2 + neighbor.dy**2);
        sumSlope += slope;
        count++;
      }
    });

    return count > 0 ? sumSlope / count : 0;
  };

  // Calculate solar potential
  const calculateSolarPotential = (solarData, elevationData, x, y) => {
    const solarValue = solarData.find(d => d.x === x && d.y === y)?.value || 0;
    const elevation = elevationData.find(d => d.x === x && d.y === y)?.value || 0;
    const slope = calculateSlope(elevationData, x, y);
    
    // Higher elevation and lower slope are better for solar
    const elevationFactor = Math.min(elevation / 1000, 1);
    const slopeFactor = Math.max(0, 1 - slope / 30); // Penalize steep slopes
    
    return solarValue * elevationFactor * slopeFactor;
  };

  // Calculate wind potential
  const calculateWindPotential = (windData, elevationData, x, y) => {
    const windValue = windData.find(d => d.x === x && d.y === y)?.value || 0;
    const elevation = elevationData.find(d => d.x === x && d.y === y)?.value || 0;
    const slope = calculateSlope(elevationData, x, y);
    
    // Higher elevation and moderate slopes are better for wind
    const elevationFactor = Math.min(elevation / 1000, 1);
    const slopeFactor = Math.max(0, 1 - Math.abs(slope - 15) / 15); // Optimal around 15 degrees
    
    return windValue * elevationFactor * slopeFactor;
  };

  // Calculate tidal potential
  const calculateTidalPotential = (x, y) => {
    // Mock tidal calculation based on distance from coast
    const distanceFromCoast = Math.min(x, y, 100 - x, 100 - y);
    return Math.max(0, 1 - distanceFromCoast / 20); // Higher near coast
  };

  // Apply constraints
  const applyConstraints = (suitability, landCoverData, elevationData, x, y) => {
    const landCover = landCoverData.find(d => d.x === x && d.y === y)?.value || 'grassland';
    const elevation = elevationData.find(d => d.x === x && d.y === y)?.value || 0;
    const slope = calculateSlope(elevationData, x, y);
    
    let constraintFactor = 1;
    
    // Exclude water bodies
    if (landCover === 'water') constraintFactor = 0;
    
    // Exclude urban areas
    if (landCover === 'urban') constraintFactor = 0;
    
    // Exclude very steep slopes (>30 degrees)
    if (slope > 30) constraintFactor = 0;
    
    // Exclude very high elevations (>1500m)
    if (elevation > 1500) constraintFactor *= 0.5;
    
    return suitability * constraintFactor;
  };

  // Analyze suitability for selected energy type
  const analyzeSuitability = async () => {
    if (!polygon) return;

    setIsAnalyzing(true);
    setAnalysisProgress(0);

    const { elevation, solarRadiation, windSpeed, rainfall, landCover } = environmentalData;
    const suitabilityMap = [];
    const candidateSpots = [];

    // Simulate analysis progress
    const totalPoints = 10000;
    let processedPoints = 0;

    for (let x = 0; x < 100; x++) {
      for (let y = 0; y < 100; y++) {
        // Check if point is within polygon (simplified)
        if (isPointInPolygon(x, y, polygon)) {
          let suitability = 0;

          switch (selectedEnergyType) {
            case 'solar':
              suitability = calculateSolarPotential(solarRadiation.data, elevation.data, x, y);
              break;
            case 'wind':
              suitability = calculateWindPotential(windSpeed.data, elevation.data, x, y);
              break;
            case 'tidal':
              suitability = calculateTidalPotential(x, y);
              break;
            case 'hydro':
              const rainfallValue = rainfall.data.find(d => d.x === x && d.y === y)?.value || 0;
              const elevationValue = elevation.data.find(d => d.x === x && d.y === y)?.value || 0;
              suitability = (rainfallValue / 1000) * (elevationValue / 1000);
              break;
            default:
              suitability = 0;
          }

          // Apply constraints
          suitability = applyConstraints(suitability, landCover.data, elevation.data, x, y);

          if (suitability > 0.3) { // Threshold for candidate spots
            candidateSpots.push({
              x, y,
              suitability,
              elevation: elevation.data.find(d => d.x === x && d.y === y)?.value || 0,
              solar: solarRadiation.data.find(d => d.x === x && d.y === y)?.value || 0,
              wind: windSpeed.data.find(d => d.x === x && d.y === y)?.value || 0,
              landCover: landCover.data.find(d => d.x === x && d.y === y)?.value || 'unknown'
            });
          }

          suitabilityMap.push({ x, y, suitability });
        }

        processedPoints++;
        if (processedPoints % 1000 === 0) {
          setAnalysisProgress((processedPoints / totalPoints) * 100);
          await new Promise(resolve => setTimeout(resolve, 10)); // Simulate processing time
        }
      }
    }

    // Sort candidate spots by suitability
    candidateSpots.sort((a, b) => b.suitability - a.suitability);

    setRecommendations({
      suitabilityMap,
      candidateSpots: candidateSpots.slice(0, 20), // Top 20 spots
      energyType: selectedEnergyType,
      totalArea: polygon.area,
      analysisDate: new Date().toISOString()
    });

    setIsAnalyzing(false);
    setAnalysisProgress(100);
  };

  // Simple point-in-polygon test (simplified for demo)
  const isPointInPolygon = (x, y, polygon) => {
    if (!polygon || polygon.length < 3) return false;
    
    // For demo purposes, check if point is in a rectangular area
    const minX = Math.min(...polygon.map(p => p.x));
    const maxX = Math.max(...polygon.map(p => p.x));
    const minY = Math.min(...polygon.map(p => p.y));
    const maxY = Math.max(...polygon.map(p => p.y));
    
    return x >= minX && x <= maxX && y >= minY && y <= maxY;
  };

  // Handle map click for polygon drawing
  const handleMapClick = (event) => {
    if (!isDrawing) return;

    const rect = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * 100;
    const y = ((event.clientY - rect.top) / rect.height) * 100;

    if (!polygon) {
      setPolygon([{ x, y }]);
    } else {
      setPolygon([...polygon, { x, y }]);
    }
  };

  // Complete polygon drawing
  const completePolygon = () => {
    if (polygon && polygon.length >= 3) {
      // Calculate area (simplified)
      const area = calculatePolygonArea(polygon);
      setPolygon([...polygon, { area }]);
      setIsDrawing(false);
    }
  };

  // Calculate polygon area (simplified)
  const calculatePolygonArea = (points) => {
    let area = 0;
    for (let i = 0; i < points.length; i++) {
      const j = (i + 1) % points.length;
      area += points[i].x * points[j].y;
      area -= points[j].x * points[i].y;
    }
    return Math.abs(area) / 2;
  };

  // Export data as GeoJSON
  const exportGeoJSON = () => {
    if (!recommendations) return;

    const geojson = {
      type: "FeatureCollection",
      features: recommendations.candidateSpots.map((spot, index) => ({
        type: "Feature",
        properties: {
          id: index + 1,
          suitability: spot.suitability,
          elevation: spot.elevation,
          solar: spot.solar,
          wind: spot.wind,
          landCover: spot.landCover,
          energyType: recommendations.energyType
        },
        geometry: {
          type: "Point",
          coordinates: [spot.x, spot.y]
        }
      }))
    };

    const blob = new Blob([JSON.stringify(geojson, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `energy-siting-${recommendations.energyType}-${new Date().toISOString().split('T')[0]}.geojson`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Export data as CSV
  const exportCSV = () => {
    if (!recommendations) return;

    const headers = ['ID', 'X', 'Y', 'Suitability', 'Elevation', 'Solar', 'Wind', 'Land Cover', 'Energy Type'];
    const rows = recommendations.candidateSpots.map((spot, index) => [
      index + 1,
      spot.x,
      spot.y,
      spot.suitability.toFixed(3),
      spot.elevation.toFixed(2),
      spot.solar.toFixed(3),
      spot.wind.toFixed(2),
      spot.landCover,
      recommendations.energyType
    ]);

    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `energy-siting-${recommendations.energyType}-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="energy-siting-container">
      <div className="siting-header">
        <h2>Renewable Energy Siting Analysis</h2>
        <p>Draw a polygon on the map to analyze optimal locations for renewable energy installations</p>
      </div>

      <div className="siting-controls">
        <div className="control-group">
          <label>Energy Type:</label>
          <select 
            value={selectedEnergyType} 
            onChange={(e) => setSelectedEnergyType(e.target.value)}
            disabled={isAnalyzing}
          >
            <option value="solar">Solar</option>
            <option value="wind">Wind</option>
            <option value="tidal">Tidal</option>
            <option value="hydro">Hydroelectric</option>
          </select>
        </div>

        <div className="control-group">
          <button 
            className={`btn-primary ${isDrawing ? 'active' : ''}`}
            onClick={() => setIsDrawing(!isDrawing)}
            disabled={isAnalyzing}
          >
            {isDrawing ? 'Stop Drawing' : 'Start Drawing'}
          </button>
        </div>

        <div className="control-group">
          <button 
            className="btn-secondary"
            onClick={completePolygon}
            disabled={!polygon || polygon.length < 3 || isAnalyzing}
          >
            Complete Polygon
          </button>
        </div>

        <div className="control-group">
          <button 
            className="btn-primary"
            onClick={analyzeSuitability}
            disabled={!polygon || isAnalyzing}
          >
            {isAnalyzing ? 'Analyzing...' : 'Analyze Suitability'}
          </button>
        </div>
      </div>

      {isAnalyzing && (
        <div className="analysis-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${analysisProgress}%` }}
            ></div>
          </div>
          <p>Processing environmental data... {Math.round(analysisProgress)}%</p>
        </div>
      )}

      <div className="map-container">
        <div 
          className="energy-map"
          ref={mapRef}
          onClick={handleMapClick}
        >
          <canvas ref={canvasRef} className="map-canvas" />
          
          {/* Draw polygon */}
          {polygon && polygon.length > 0 && (
            <svg className="polygon-overlay">
              <polyline
                points={polygon.map(p => `${p.x}%,${p.y}%`).join(' ')}
                fill="none"
                stroke="#2DD4BF"
                strokeWidth="2"
                strokeDasharray="5,5"
              />
              {polygon.map((point, index) => (
                <circle
                  key={index}
                  cx={`${point.x}%`}
                  cy={`${point.y}%`}
                  r="3"
                  fill="#2DD4BF"
                />
              ))}
            </svg>
          )}

          {/* Draw suitability heatmap */}
          {recommendations && (
            <div className="suitability-overlay">
              {recommendations.suitabilityMap.map((point, index) => (
                <div
                  key={index}
                  className="suitability-point"
                  style={{
                    left: `${point.x}%`,
                    top: `${point.y}%`,
                    opacity: point.suitability,
                    backgroundColor: point.suitability > 0.7 ? '#10B981' : 
                                   point.suitability > 0.4 ? '#F59E0B' : '#EF4444'
                  }}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {recommendations && (
        <div className="recommendations-panel">
          <div className="recommendations-header">
            <h3>Top Recommendations for {recommendations.energyType.charAt(0).toUpperCase() + recommendations.energyType.slice(1)}</h3>
            <div className="export-buttons">
              <button className="btn-secondary" onClick={exportGeoJSON}>
                Export GeoJSON
              </button>
              <button className="btn-secondary" onClick={exportCSV}>
                Export CSV
              </button>
            </div>
          </div>

          <div className="recommendations-grid">
            {recommendations.candidateSpots.slice(0, 10).map((spot, index) => (
              <div key={index} className="recommendation-card">
                <div className="spot-header">
                  <h4>Spot #{index + 1}</h4>
                  <div className="suitability-score">
                    {(spot.suitability * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="spot-metrics">
                  <div className="metric">
                    <span className="metric-label">Elevation:</span>
                    <span className="metric-value">{spot.elevation.toFixed(0)}m</span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Solar Radiation:</span>
                    <span className="metric-value">{spot.solar.toFixed(2)} kWh/m²/day</span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Wind Speed:</span>
                    <span className="metric-value">{spot.wind.toFixed(1)} m/s</span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Land Cover:</span>
                    <span className="metric-value">{spot.landCover}</span>
                  </div>
                </div>
                <div className="spot-coordinates">
                  Coordinates: ({spot.x.toFixed(1)}, {spot.y.toFixed(1)})
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default EnergySitingMap;
