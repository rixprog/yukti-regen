// Environmental Data Processing Utilities for Energy Siting

export class EnvironmentalDataProcessor {
  constructor() {
    this.dataCache = new Map();
    this.analysisCache = new Map();
  }

  // Process elevation data to calculate slope and aspect
  calculateTerrainMetrics(elevationData, cellSize = 1) {
    const slopes = [];
    const aspects = [];
    
    for (let i = 0; i < elevationData.length; i++) {
      const point = elevationData[i];
      const { x, y, value: elevation } = point;
      
      // Calculate slope using 3x3 neighborhood
      const slope = this.calculateSlope(elevationData, x, y, cellSize);
      const aspect = this.calculateAspect(elevationData, x, y, cellSize);
      
      slopes.push({ x, y, value: slope });
      aspects.push({ x, y, value: aspect });
    }
    
    return { slopes, aspects };
  }

  // Calculate slope from elevation data using Horn's algorithm
  calculateSlope(elevationData, x, y, cellSize) {
    const neighbors = this.getNeighbors(elevationData, x, y);
    if (neighbors.length < 8) return 0;

    const [nw, n, ne, w, e, sw, s, se] = neighbors;
    
    const dz_dx = ((ne + 2*e + se) - (nw + 2*w + sw)) / (8 * cellSize);
    const dz_dy = ((sw + 2*s + se) - (nw + 2*n + ne)) / (8 * cellSize);
    
    const slope = Math.atan(Math.sqrt(dz_dx*dz_dx + dz_dy*dz_dy)) * (180 / Math.PI);
    return slope;
  }

  // Calculate aspect from elevation data
  calculateAspect(elevationData, x, y, cellSize) {
    const neighbors = this.getNeighbors(elevationData, x, y);
    if (neighbors.length < 8) return 0;

    const [nw, n, ne, w, e, sw, s, se] = neighbors;
    
    const dz_dx = ((ne + 2*e + se) - (nw + 2*w + sw)) / (8 * cellSize);
    const dz_dy = ((sw + 2*s + se) - (nw + 2*n + ne)) / (8 * cellSize);
    
    let aspect = Math.atan2(dz_dy, -dz_dx) * (180 / Math.PI);
    if (aspect < 0) aspect += 360;
    
    return aspect;
  }

  // Get 8-neighborhood values
  getNeighbors(data, x, y) {
    const neighbors = [];
    const offsets = [
      [-1, -1], [0, -1], [1, -1],
      [-1, 0],           [1, 0],
      [-1, 1],  [0, 1],  [1, 1]
    ];
    
    offsets.forEach(([dx, dy]) => {
      const neighbor = data.find(d => d.x === x + dx && d.y === y + dy);
      neighbors.push(neighbor ? neighbor.value : 0);
    });
    
    return neighbors;
  }

  // Calculate solar potential considering multiple factors
  calculateSolarPotential(solarData, elevationData, slopeData, aspectData, latitude = 40) {
    const solarPotential = [];
    
    for (let i = 0; i < solarData.length; i++) {
      const solar = solarData[i];
      const elevation = elevationData.find(d => d.x === solar.x && d.y === solar.y);
      const slope = slopeData.find(d => d.x === solar.x && d.y === solar.y);
      const aspect = aspectData.find(d => d.x === solar.x && d.y === solar.y);
      
      if (!elevation || !slope || !aspect) continue;
      
      // Base solar radiation
      let potential = solar.value;
      
      // Elevation factor (higher is better, but with diminishing returns)
      const elevationFactor = Math.min(1, elevation.value / 1000);
      potential *= (0.8 + 0.2 * elevationFactor);
      
      // Slope factor (optimal around 30-35 degrees for most latitudes)
      const optimalSlope = Math.max(0, latitude - 15);
      const slopeFactor = Math.max(0, 1 - Math.abs(slope.value - optimalSlope) / 45);
      potential *= slopeFactor;
      
      // Aspect factor (south-facing is best in northern hemisphere)
      const aspectFactor = this.calculateAspectFactor(aspect.value, latitude);
      potential *= aspectFactor;
      
      // Shading factor (simplified)
      const shadingFactor = this.calculateShadingFactor(elevationData, solar.x, solar.y);
      potential *= shadingFactor;
      
      solarPotential.push({
        x: solar.x,
        y: solar.y,
        value: Math.max(0, potential),
        factors: {
          base: solar.value,
          elevation: elevationFactor,
          slope: slopeFactor,
          aspect: aspectFactor,
          shading: shadingFactor
        }
      });
    }
    
    return solarPotential;
  }

  // Calculate wind potential considering terrain effects
  calculateWindPotential(windData, elevationData, slopeData, landCoverData) {
    const windPotential = [];
    
    for (let i = 0; i < windData.length; i++) {
      const wind = windData[i];
      const elevation = elevationData.find(d => d.x === wind.x && d.y === wind.y);
      const slope = slopeData.find(d => d.x === wind.x && d.y === wind.y);
      const landCover = landCoverData.find(d => d.x === wind.x && d.y === wind.y);
      
      if (!elevation || !slope || !landCover) continue;
      
      // Base wind speed
      let potential = wind.value;
      
      // Elevation factor (wind speed increases with height)
      const elevationFactor = 1 + (elevation.value / 1000) * 0.1;
      potential *= elevationFactor;
      
      // Slope factor (moderate slopes are better)
      const slopeFactor = Math.max(0, 1 - Math.abs(slope.value - 15) / 30);
      potential *= slopeFactor;
      
      // Land cover factor
      const landCoverFactor = this.getLandCoverWindFactor(landCover.value);
      potential *= landCoverFactor;
      
      // Terrain roughness factor
      const roughnessFactor = this.calculateRoughnessFactor(elevationData, wind.x, wind.y);
      potential *= roughnessFactor;
      
      windPotential.push({
        x: wind.x,
        y: wind.y,
        value: Math.max(0, potential),
        factors: {
          base: wind.value,
          elevation: elevationFactor,
          slope: slopeFactor,
          landCover: landCoverFactor,
          roughness: roughnessFactor
        }
      });
    }
    
    return windPotential;
  }

  // Calculate tidal potential based on coastal proximity and bathymetry
  calculateTidalPotential(coastalData, bathymetryData, currentData) {
    const tidalPotential = [];
    
    for (let i = 0; i < coastalData.length; i++) {
      const coastal = coastalData[i];
      const bathymetry = bathymetryData.find(d => d.x === coastal.x && d.y === coastal.y);
      const current = currentData.find(d => d.x === coastal.x && d.y === coastal.y);
      
      if (!bathymetry || !current) continue;
      
      // Distance from coast factor
      const distanceFactor = Math.max(0, 1 - coastal.value / 50); // Within 50km of coast
      
      // Bathymetry factor (optimal depth 20-50m)
      const depth = Math.abs(bathymetry.value);
      const depthFactor = depth >= 20 && depth <= 50 ? 1 : 
                         depth < 20 ? depth / 20 : 
                         Math.max(0, 1 - (depth - 50) / 100);
      
      // Current strength factor
      const currentFactor = Math.min(1, current.value / 2); // Normalize to 0-1
      
      const potential = distanceFactor * depthFactor * currentFactor;
      
      tidalPotential.push({
        x: coastal.x,
        y: coastal.y,
        value: potential,
        factors: {
          distance: distanceFactor,
          depth: depthFactor,
          current: currentFactor
        }
      });
    }
    
    return tidalPotential;
  }

  // Calculate hydroelectric potential
  calculateHydroPotential(elevationData, rainfallData, streamData) {
    const hydroPotential = [];
    
    for (let i = 0; i < elevationData.length; i++) {
      const elevation = elevationData[i];
      const rainfall = rainfallData.find(d => d.x === elevation.x && d.y === elevation.y);
      const stream = streamData.find(d => d.x === elevation.x && d.y === elevation.y);
      
      if (!rainfall || !stream) continue;
      
      // Head factor (elevation difference)
      const headFactor = Math.min(1, elevation.value / 1000);
      
      // Flow factor (rainfall and stream data)
      const flowFactor = Math.min(1, (rainfall.value / 1000) * (stream.value / 10));
      
      // Stream density factor
      const streamFactor = Math.min(1, stream.value / 5);
      
      const potential = headFactor * flowFactor * streamFactor;
      
      hydroPotential.push({
        x: elevation.x,
        y: elevation.y,
        value: potential,
        factors: {
          head: headFactor,
          flow: flowFactor,
          stream: streamFactor
        }
      });
    }
    
    return hydroPotential;
  }

  // Apply constraints to suitability analysis
  applyConstraints(suitabilityData, constraints) {
    const { 
      protectedAreas = [],
      waterBodies = [],
      urbanAreas = [],
      maxSlope = 30,
      minElevation = 0,
      maxElevation = 2000,
      landCoverRestrictions = []
    } = constraints;
    
    return suitabilityData.map(point => {
      let constraintFactor = 1;
      
      // Check protected areas
      if (this.isInPolygon(point, protectedAreas)) {
        constraintFactor = 0;
      }
      
      // Check water bodies
      if (this.isInPolygon(point, waterBodies)) {
        constraintFactor = 0;
      }
      
      // Check urban areas
      if (this.isInPolygon(point, urbanAreas)) {
        constraintFactor = 0;
      }
      
      // Check elevation constraints
      if (point.elevation < minElevation || point.elevation > maxElevation) {
        constraintFactor *= 0.5;
      }
      
      // Check slope constraints
      if (point.slope > maxSlope) {
        constraintFactor = 0;
      }
      
      // Check land cover restrictions
      if (landCoverRestrictions.includes(point.landCover)) {
        constraintFactor = 0;
      }
      
      return {
        ...point,
        value: point.value * constraintFactor,
        constraintFactor
      };
    });
  }

  // Normalize data to 0-1 range
  normalizeData(data, method = 'minmax') {
    if (data.length === 0) return data;
    
    const values = data.map(d => d.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    
    if (max === min) return data.map(d => ({ ...d, value: 0.5 }));
    
    return data.map(d => ({
      ...d,
      value: (d.value - min) / (max - min)
    }));
  }

  // Weighted combination of multiple factors
  combineFactors(factors, weights) {
    const totalWeight = Object.values(weights).reduce((sum, weight) => sum + weight, 0);
    
    return factors.map(factor => {
      let combinedValue = 0;
      Object.keys(weights).forEach(key => {
        if (factor[key] !== undefined) {
          combinedValue += factor[key] * weights[key];
        }
      });
      
      return {
        ...factor,
        value: combinedValue / totalWeight
      };
    });
  }

  // Helper methods
  calculateAspectFactor(aspect, latitude) {
    // South-facing is optimal in northern hemisphere
    const southAspect = 180;
    const aspectDiff = Math.abs(aspect - southAspect);
    return Math.max(0, 1 - aspectDiff / 180);
  }

  calculateShadingFactor(elevationData, x, y) {
    // Simplified shading calculation
    const currentElev = elevationData.find(d => d.x === x && d.y === y)?.value || 0;
    const neighbors = this.getNeighbors(elevationData, x, y);
    const maxNeighborElev = Math.max(...neighbors);
    
    return maxNeighborElev > currentElev ? 0.8 : 1.0;
  }

  getLandCoverWindFactor(landCover) {
    const factors = {
      'water': 1.0,
      'grassland': 0.9,
      'agricultural': 0.8,
      'forest': 0.6,
      'urban': 0.4,
      'mountain': 0.7
    };
    
    return factors[landCover] || 0.5;
  }

  calculateRoughnessFactor(elevationData, x, y) {
    // Calculate surface roughness based on elevation variance
    const neighbors = this.getNeighbors(elevationData, x, y);
    const currentElev = elevationData.find(d => d.x === x && d.y === y)?.value || 0;
    
    const variance = neighbors.reduce((sum, elev) => sum + Math.pow(elev - currentElev, 2), 0) / neighbors.length;
    const roughness = Math.sqrt(variance);
    
    return Math.max(0.5, 1 - roughness / 100);
  }

  isInPolygon(point, polygon) {
    if (!polygon || polygon.length < 3) return false;
    
    let inside = false;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      if (((polygon[i].y > point.y) !== (polygon[j].y > point.y)) &&
          (point.x < (polygon[j].x - polygon[i].x) * (point.y - polygon[i].y) / (polygon[j].y - polygon[i].y) + polygon[i].x)) {
        inside = !inside;
      }
    }
    
    return inside;
  }

  // Generate mock data for testing
  generateMockData(width = 100, height = 100) {
    const elevationData = [];
    const solarData = [];
    const windData = [];
    const rainfallData = [];
    const landCoverData = [];
    
    for (let x = 0; x < width; x++) {
      for (let y = 0; y < height; y++) {
        // Elevation with some terrain features
        const elevation = 100 + Math.sin(x * 0.1) * 200 + Math.cos(y * 0.1) * 150 + Math.random() * 100;
        
        // Solar radiation with seasonal variation
        const solar = 3 + Math.sin(x * 0.05) * 1.5 + Math.random() * 2;
        
        // Wind speed with terrain effects
        const wind = 5 + Math.cos(y * 0.08) * 3 + Math.random() * 5;
        
        // Rainfall with geographic patterns
        const rainfall = 500 + Math.sin(x * 0.03) * 300 + Math.random() * 400;
        
        // Land cover types
        const landCoverTypes = ['forest', 'grassland', 'urban', 'water', 'agricultural'];
        const landCover = landCoverTypes[Math.floor(Math.random() * landCoverTypes.length)];
        
        elevationData.push({ x, y, value: elevation });
        solarData.push({ x, y, value: solar });
        windData.push({ x, y, value: wind });
        rainfallData.push({ x, y, value: rainfall });
        landCoverData.push({ x, y, value: landCover });
      }
    }
    
    return {
      elevation: elevationData,
      solar: solarData,
      wind: windData,
      rainfall: rainfallData,
      landCover: landCoverData
    };
  }
}

export default EnvironmentalDataProcessor;
