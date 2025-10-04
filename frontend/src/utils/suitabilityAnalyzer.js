// Suitability Analysis Engine for Renewable Energy Siting

export class SuitabilityAnalyzer {
  constructor() {
    this.energyTypeWeights = {
      solar: {
        solarRadiation: 0.4,
        elevation: 0.2,
        slope: 0.15,
        aspect: 0.1,
        landCover: 0.1,
        infrastructure: 0.05
      },
      wind: {
        windSpeed: 0.4,
        elevation: 0.2,
        slope: 0.15,
        landCover: 0.15,
        infrastructure: 0.1
      },
      tidal: {
        coastalProximity: 0.5,
        bathymetry: 0.3,
        currentStrength: 0.2
      },
      hydro: {
        elevation: 0.3,
        rainfall: 0.25,
        streamDensity: 0.25,
        slope: 0.2
      }
    };

    this.constraintMasks = {
      protectedAreas: true,
      waterBodies: true,
      urbanAreas: true,
      maxSlope: 30,
      minElevation: 0,
      maxElevation: 2000,
      landCoverRestrictions: ['water', 'urban']
    };
  }

  // Main analysis function
  async analyzeSuitability(polygon, energyType, environmentalData, options = {}) {
    const startTime = performance.now();
    
    try {
      // Step 1: Clip data to polygon
      const clippedData = this.clipDataToPolygon(environmentalData, polygon);
      
      // Step 2: Calculate derived indicators
      const derivedIndicators = await this.calculateDerivedIndicators(clippedData, energyType);
      
      // Step 3: Normalize factors
      const normalizedFactors = this.normalizeFactors(derivedIndicators, energyType);
      
      // Step 4: Apply constraint masks
      const constrainedFactors = this.applyConstraintMasks(normalizedFactors, this.constraintMasks);
      
      // Step 5: Calculate weighted suitability
      const suitabilityScores = this.calculateWeightedSuitability(constrainedFactors, energyType);
      
      // Step 6: Generate heatmap data
      const heatmapData = this.generateHeatmapData(suitabilityScores, polygon);
      
      // Step 7: Identify and rank candidate spots
      const candidateSpots = this.identifyCandidateSpots(suitabilityScores, options.topN || 20);
      
      // Step 8: Generate analysis report
      const analysisReport = this.generateAnalysisReport(
        candidateSpots, 
        energyType, 
        polygon, 
        performance.now() - startTime
      );
      
      return {
        suitabilityMap: heatmapData,
        candidateSpots,
        analysisReport,
        energyType,
        polygon,
        timestamp: new Date().toISOString(),
        processingTime: performance.now() - startTime
      };
      
    } catch (error) {
      console.error('Suitability analysis failed:', error);
      throw new Error(`Analysis failed: ${error.message}`);
    }
  }

  // Clip environmental data to polygon boundary
  clipDataToPolygon(environmentalData, polygon) {
    const clippedData = {};
    
    Object.keys(environmentalData).forEach(dataType => {
      clippedData[dataType] = environmentalData[dataType].filter(point => 
        this.isPointInPolygon(point, polygon)
      );
    });
    
    return clippedData;
  }

  // Calculate derived indicators based on energy type
  async calculateDerivedIndicators(data, energyType) {
    const indicators = {};
    
    // Common indicators for all energy types
    if (data.elevation) {
      indicators.elevation = data.elevation;
      indicators.slope = this.calculateSlope(data.elevation);
      indicators.aspect = this.calculateAspect(data.elevation);
    }
    
    // Energy-specific indicators
    switch (energyType) {
      case 'solar':
        indicators.solarRadiation = data.solar || [];
        indicators.solarPotential = this.calculateSolarPotential(data, indicators);
        indicators.shading = this.calculateShading(data.elevation);
        break;
        
      case 'wind':
        indicators.windSpeed = data.wind || [];
        indicators.windPotential = this.calculateWindPotential(data, indicators);
        indicators.roughness = this.calculateRoughness(data.elevation);
        break;
        
      case 'tidal':
        indicators.coastalProximity = this.calculateCoastalProximity(data);
        indicators.bathymetry = data.bathymetry || [];
        indicators.currentStrength = data.current || [];
        break;
        
      case 'hydro':
        indicators.rainfall = data.rainfall || [];
        indicators.streamDensity = data.streams || [];
        indicators.watershedArea = this.calculateWatershedArea(data.elevation);
        break;
    }
    
    // Infrastructure indicators
    indicators.infrastructure = this.calculateInfrastructureProximity(data);
    
    return indicators;
  }

  // Calculate slope from elevation data
  calculateSlope(elevationData) {
    return elevationData.map(point => {
      const slope = this.computeSlopeAtPoint(elevationData, point.x, point.y);
      return { ...point, value: slope };
    });
  }

  // Calculate aspect from elevation data
  calculateAspect(elevationData) {
    return elevationData.map(point => {
      const aspect = this.computeAspectAtPoint(elevationData, point.x, point.y);
      return { ...point, value: aspect };
    });
  }

  // Calculate solar potential
  calculateSolarPotential(data, indicators) {
    const solarData = data.solar || [];
    const elevationData = data.elevation || [];
    const slopeData = indicators.slope || [];
    const aspectData = indicators.aspect || [];
    
    return solarData.map(solar => {
      const elevation = elevationData.find(e => e.x === solar.x && e.y === solar.y);
      const slope = slopeData.find(s => s.x === solar.x && s.y === solar.y);
      const aspect = aspectData.find(a => a.x === solar.x && a.y === solar.y);
      
      if (!elevation || !slope || !aspect) return { ...solar, value: 0 };
      
      // Solar potential calculation
      let potential = solar.value;
      
      // Elevation factor (higher is better, but with diminishing returns)
      const elevationFactor = Math.min(1, elevation.value / 1000);
      potential *= (0.8 + 0.2 * elevationFactor);
      
      // Slope factor (optimal around 30-35 degrees)
      const optimalSlope = 32;
      const slopeFactor = Math.max(0, 1 - Math.abs(slope.value - optimalSlope) / 45);
      potential *= slopeFactor;
      
      // Aspect factor (south-facing is best)
      const aspectFactor = this.calculateAspectFactor(aspect.value);
      potential *= aspectFactor;
      
      return { ...solar, value: Math.max(0, potential) };
    });
  }

  // Calculate wind potential
  calculateWindPotential(data, indicators) {
    const windData = data.wind || [];
    const elevationData = data.elevation || [];
    const slopeData = indicators.slope || [];
    const landCoverData = data.landCover || [];
    
    return windData.map(wind => {
      const elevation = elevationData.find(e => e.x === wind.x && e.y === wind.y);
      const slope = slopeData.find(s => s.x === wind.x && s.y === wind.y);
      const landCover = landCoverData.find(l => l.x === wind.x && l.y === wind.y);
      
      if (!elevation || !slope || !landCover) return { ...wind, value: 0 };
      
      // Wind potential calculation
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
      
      return { ...wind, value: Math.max(0, potential) };
    });
  }

  // Calculate tidal potential
  calculateTidalPotential(data, indicators) {
    const coastalProximity = indicators.coastalProximity || [];
    const bathymetry = indicators.bathymetry || [];
    const currentStrength = indicators.currentStrength || [];
    
    return coastalProximity.map(coastal => {
      const bath = bathymetry.find(b => b.x === coastal.x && b.y === coastal.y);
      const current = currentStrength.find(c => c.x === coastal.x && c.y === coastal.y);
      
      if (!bath || !current) return { ...coastal, value: 0 };
      
      // Tidal potential calculation
      const distanceFactor = Math.max(0, 1 - coastal.value / 50);
      const depth = Math.abs(bath.value);
      const depthFactor = depth >= 20 && depth <= 50 ? 1 : 
                         depth < 20 ? depth / 20 : 
                         Math.max(0, 1 - (depth - 50) / 100);
      const currentFactor = Math.min(1, current.value / 2);
      
      const potential = distanceFactor * depthFactor * currentFactor;
      
      return { ...coastal, value: potential };
    });
  }

  // Calculate hydroelectric potential
  calculateHydroPotential(data, indicators) {
    const elevationData = data.elevation || [];
    const rainfallData = indicators.rainfall || [];
    const streamData = indicators.streamDensity || [];
    const slopeData = indicators.slope || [];
    
    return elevationData.map(elevation => {
      const rainfall = rainfallData.find(r => r.x === elevation.x && r.y === elevation.y);
      const stream = streamData.find(s => s.x === elevation.x && s.y === elevation.y);
      const slope = slopeData.find(s => s.x === elevation.x && s.y === elevation.y);
      
      if (!rainfall || !stream || !slope) return { ...elevation, value: 0 };
      
      // Hydro potential calculation
      const headFactor = Math.min(1, elevation.value / 1000);
      const flowFactor = Math.min(1, (rainfall.value / 1000) * (stream.value / 10));
      const streamFactor = Math.min(1, stream.value / 5);
      const slopeFactor = Math.max(0, 1 - Math.abs(slope.value - 20) / 40);
      
      const potential = headFactor * flowFactor * streamFactor * slopeFactor;
      
      return { ...elevation, value: potential };
    });
  }

  // Normalize factors to 0-1 range
  normalizeFactors(indicators, energyType) {
    const normalized = {};
    
    Object.keys(indicators).forEach(key => {
      const data = indicators[key];
      if (!data || data.length === 0) return;
      
      const values = data.map(d => d.value);
      const min = Math.min(...values);
      const max = Math.max(...values);
      
      if (max === min) {
        normalized[key] = data.map(d => ({ ...d, value: 0.5 }));
      } else {
        normalized[key] = data.map(d => ({
          ...d,
          value: (d.value - min) / (max - min)
        }));
      }
    });
    
    return normalized;
  }

  // Apply constraint masks
  applyConstraintMasks(factors, constraints) {
    const constrained = {};
    
    Object.keys(factors).forEach(key => {
      constrained[key] = factors[key].map(point => {
        let constraintFactor = 1;
        
        // Apply various constraints
        if (constraints.maxSlope && point.slope > constraints.maxSlope) {
          constraintFactor = 0;
        }
        
        if (constraints.minElevation && point.elevation < constraints.minElevation) {
          constraintFactor *= 0.5;
        }
        
        if (constraints.maxElevation && point.elevation > constraints.maxElevation) {
          constraintFactor *= 0.5;
        }
        
        if (constraints.landCoverRestrictions && 
            constraints.landCoverRestrictions.includes(point.landCover)) {
          constraintFactor = 0;
        }
        
        return {
          ...point,
          value: point.value * constraintFactor,
          constraintFactor
        };
      });
    });
    
    return constrained;
  }

  // Calculate weighted suitability scores
  calculateWeightedSuitability(factors, energyType) {
    const weights = this.energyTypeWeights[energyType] || {};
    const suitabilityScores = [];
    
    // Get all unique coordinates
    const coordinates = new Set();
    Object.values(factors).forEach(data => {
      data.forEach(point => {
        coordinates.add(`${point.x},${point.y}`);
      });
    });
    
    coordinates.forEach(coord => {
      const [x, y] = coord.split(',').map(Number);
      let weightedScore = 0;
      let totalWeight = 0;
      
      Object.keys(weights).forEach(factorName => {
        const factorData = factors[factorName];
        if (factorData) {
          const point = factorData.find(p => p.x === x && p.y === y);
          if (point) {
            weightedScore += point.value * weights[factorName];
            totalWeight += weights[factorName];
          }
        }
      });
      
      if (totalWeight > 0) {
        suitabilityScores.push({
          x,
          y,
          value: weightedScore / totalWeight,
          factors: this.extractFactorValues(factors, x, y)
        });
      }
    });
    
    return suitabilityScores;
  }

  // Generate heatmap data
  generateHeatmapData(suitabilityScores, polygon) {
    return suitabilityScores.map(point => ({
      ...point,
      inPolygon: this.isPointInPolygon(point, polygon)
    }));
  }

  // Identify and rank candidate spots
  identifyCandidateSpots(suitabilityScores, topN = 20) {
    return suitabilityScores
      .filter(point => point.value > 0.3) // Minimum threshold
      .sort((a, b) => b.value - a.value)
      .slice(0, topN)
      .map((point, index) => ({
        ...point,
        rank: index + 1,
        suitability: point.value,
        explanation: this.generateExplanation(point)
      }));
  }

  // Generate analysis report
  generateAnalysisReport(candidateSpots, energyType, polygon, processingTime) {
    const totalArea = this.calculatePolygonArea(polygon);
    const avgSuitability = candidateSpots.reduce((sum, spot) => sum + spot.value, 0) / candidateSpots.length;
    const maxSuitability = Math.max(...candidateSpots.map(spot => spot.value));
    
    return {
      energyType,
      totalArea,
      candidateCount: candidateSpots.length,
      averageSuitability: avgSuitability,
      maxSuitability,
      processingTime,
      recommendations: this.generateRecommendations(candidateSpots, energyType)
    };
  }

  // Helper methods
  isPointInPolygon(point, polygon) {
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

  calculatePolygonArea(polygon) {
    let area = 0;
    for (let i = 0; i < polygon.length; i++) {
      const j = (i + 1) % polygon.length;
      area += polygon[i].x * polygon[j].y;
      area -= polygon[j].x * polygon[i].y;
    }
    return Math.abs(area) / 2;
  }

  computeSlopeAtPoint(elevationData, x, y) {
    // Simplified slope calculation
    const neighbors = this.getNeighbors(elevationData, x, y);
    if (neighbors.length < 8) return 0;
    
    const [nw, n, ne, w, e, sw, s, se] = neighbors;
    const dz_dx = ((ne + 2*e + se) - (nw + 2*w + sw)) / 8;
    const dz_dy = ((sw + 2*s + se) - (nw + 2*n + ne)) / 8;
    
    return Math.atan(Math.sqrt(dz_dx*dz_dx + dz_dy*dz_dy)) * (180 / Math.PI);
  }

  computeAspectAtPoint(elevationData, x, y) {
    const neighbors = this.getNeighbors(elevationData, x, y);
    if (neighbors.length < 8) return 0;
    
    const [nw, n, ne, w, e, sw, s, se] = neighbors;
    const dz_dx = ((ne + 2*e + se) - (nw + 2*w + sw)) / 8;
    const dz_dy = ((sw + 2*s + se) - (nw + 2*n + ne)) / 8;
    
    let aspect = Math.atan2(dz_dy, -dz_dx) * (180 / Math.PI);
    if (aspect < 0) aspect += 360;
    
    return aspect;
  }

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

  calculateAspectFactor(aspect) {
    const southAspect = 180;
    const aspectDiff = Math.abs(aspect - southAspect);
    return Math.max(0, 1 - aspectDiff / 180);
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

  extractFactorValues(factors, x, y) {
    const values = {};
    Object.keys(factors).forEach(key => {
      const point = factors[key].find(p => p.x === x && p.y === y);
      if (point) {
        values[key] = point.value;
      }
    });
    return values;
  }

  generateExplanation(point) {
    const factors = point.factors || {};
    const explanations = [];
    
    if (factors.solarRadiation > 0.7) explanations.push('High solar radiation');
    if (factors.elevation > 0.7) explanations.push('Optimal elevation');
    if (factors.slope > 0.7) explanations.push('Suitable slope');
    if (factors.windSpeed > 0.7) explanations.push('Strong wind resources');
    if (factors.infrastructure > 0.7) explanations.push('Good infrastructure access');
    
    return explanations.length > 0 ? explanations.join(', ') : 'Moderate suitability';
  }

  generateRecommendations(candidateSpots, energyType) {
    if (candidateSpots.length === 0) {
      return ['No suitable locations found within the specified area'];
    }
    
    const recommendations = [];
    const topSpot = candidateSpots[0];
    
    recommendations.push(`Best location: ${topSpot.x.toFixed(1)}, ${topSpot.y.toFixed(1)} (${(topSpot.suitability * 100).toFixed(1)}% suitability)`);
    
    if (candidateSpots.length > 1) {
      recommendations.push(`${candidateSpots.length} suitable locations identified`);
    }
    
    const avgSuitability = candidateSpots.reduce((sum, spot) => sum + spot.suitability, 0) / candidateSpots.length;
    if (avgSuitability > 0.7) {
      recommendations.push('High overall suitability for ' + energyType + ' energy');
    } else if (avgSuitability > 0.4) {
      recommendations.push('Moderate suitability for ' + energyType + ' energy');
    } else {
      recommendations.push('Consider alternative energy types or expand search area');
    }
    
    return recommendations;
  }
}

export default SuitabilityAnalyzer;
