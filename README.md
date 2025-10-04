# Carbon Footprint Visualizer

A comprehensive web application for tracking and visualizing carbon footprint from commuting and energy consumption. Features IoT integration with ESP32 and ACS712 current sensor for real-time energy monitoring.

## 🌱 Features

- **Commute Tracking**: Log different transport modes with automatic CO₂ calculations
- **Energy Monitoring**: Track power consumption with IoT sensors
- **Real-time Visualization**: Interactive charts and analytics dashboard
- **IoT Integration**: ESP32 + ACS712 current sensor for automated data collection
- **Monthly Reports**: Aggregated data analysis and trends
- **Modern UI**: Beautiful, responsive React frontend

## 🏗️ Architecture

- **Frontend**: React with Recharts for visualization
- **Backend**: FastAPI with SQLite database
- **IoT**: ESP32 with ACS712 current sensor
- **Communication**: UDP for IoT data transmission

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- ESP32 development board
- ACS712 current sensor (30A version)
- 9W LED bulb

### Backend Setup

1. **Navigate to backend directory**:

   ```bash
   cd backend
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Start the FastAPI server**:

   ```bash
   python main.py
   ```

4. **Start the UDP server** (in another terminal):
   ```bash
   python udp_server.py
   ```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**:

   ```bash
   cd frontend
   ```

2. **Install dependencies**:

   ```bash
   npm install
   ```

3. **Start the React development server**:
   ```bash
   npm start
   ```

The frontend will be available at `http://localhost:3000`

## 🔧 IoT Setup

### Hardware Connections

```
ESP32          ACS712
------         ------
3.3V    ->     VCC
GND     ->     GND
GPIO34  ->     OUT
```

### ESP32 Code Setup

1. **Install Arduino IDE** and ESP32 board support
2. **Install required libraries**:
   - WiFi
   - ArduinoJson
3. **Update the code** in `esp32_example.ino`:
   - Change WiFi credentials
   - Update server IP address
4. **Upload to ESP32**

### Calibration

The ACS712 sensor needs calibration for accurate readings:

1. **Zero current calibration**: Measure voltage when no current flows
2. **Adjust sensitivity**: Fine-tune based on known load (9W bulb)
3. **Test with multimeter**: Compare readings for accuracy

## 📊 API Endpoints

### Commute Logs

- `POST /api/commute-logs` - Add commute log
- `GET /api/commute-logs` - Get all commute logs

### Energy Logs

- `POST /api/energy-logs` - Add energy consumption log
- `GET /api/energy-logs` - Get all energy logs

### Analytics

- `GET /api/monthly-data` - Get monthly aggregated data
- `GET /api/dashboard-stats` - Get dashboard statistics

### IoT Integration

- UDP server listens on port 8888 for IoT data

## 🎯 Usage

### Manual Data Entry

1. **Commute Logging**:

   - Select transport mode (car, bus, train, etc.)
   - Enter distance in kilometers
   - System automatically calculates CO₂ emissions

2. **Energy Logging**:
   - Enter power consumption in watts
   - Enter duration in hours
   - System calculates energy (kWh) and CO₂ emissions

### IoT Data Collection

1. **ESP32 Setup**:

   - Connect ACS712 sensor to measure current
   - Connect 9W bulb to relay
   - Configure WiFi and server IP

2. **Automated Monitoring**:
   - Send "start" command to begin monitoring
   - ESP32 measures current and calculates power
   - Data automatically sent to server via UDP
   - Send "stop" command to end session

### Dashboard Features

- **Real-time Statistics**: Total and monthly CO₂ emissions
- **Interactive Charts**: Monthly trends and distribution
- **Data Tables**: Detailed logs with filtering
- **Responsive Design**: Works on desktop and mobile

## 🧮 Carbon Footprint Calculations

### Commute Emissions (kg CO₂/km)

- Car: 0.192
- Motorcycle: 0.103
- Bus: 0.089
- Train: 0.041
- Bicycle: 0.0
- Walking: 0.0
- Electric Car: 0.053
- Hybrid Car: 0.120

### Energy Emissions

- Grid electricity: 0.5 kg CO₂/kWh (adjust for your region)

## 🔌 IoT Data Format

### Energy Data

```json
{
  "type": "energy",
  "device_id": "esp32_001",
  "power_watts": 9.2,
  "duration_hours": 2.5,
  "energy_kwh": 0.023,
  "timestamp": "2024-01-15T14:30:00"
}
```

### Commute Data

```json
{
  "type": "commute",
  "device_id": "gps_tracker_001",
  "distance_km": 15.5,
  "transport_mode": "car",
  "timestamp": "2024-01-15T14:30:00"
}
```

## 🛠️ Development

### Project Structure

```
carbon-footprint-visualizer/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── udp_server.py        # IoT data receiver
│   ├── requirements.txt     # Python dependencies
│   └── esp32_example.ino    # ESP32 Arduino code
├── frontend/
│   ├── src/
│   │   ├── App.js           # Main React component
│   │   ├── index.js         # React entry point
│   │   └── index.css        # Styling
│   └── package.json         # Node.js dependencies
└── README.md
```

### Database Schema

**commute_logs**:

- id, date, transport_mode, distance_km, co2_emissions_kg, created_at

**energy_consumption**:

- id, date, power_consumption_watts, duration_hours, energy_kwh, co2_emissions_kg, created_at

**monthly_aggregations**:

- id, year, month, total_commute_co2, total_energy_co2, total_co2, commute_distance_km, energy_consumption_kwh

## 🚀 Deployment

### Production Setup

1. **Backend**:

   ```bash
   pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
   ```

2. **Frontend**:

   ```bash
   npm run build
   # Serve static files with nginx or similar
   ```

3. **Database**: Consider PostgreSQL for production

### Docker Deployment

```dockerfile
# Backend Dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is open source and available under the MIT License.

## 🔮 Future Enhancements

- [ ] Real-time notifications
- [ ] Mobile app (React Native)
- [ ] Machine learning predictions
- [ ] Social sharing features
- [ ] Carbon offset recommendations
- [ ] Advanced analytics
- [ ] Multi-user support
- [ ] API authentication
- [ ] Data export (CSV, PDF)
- [ ] Integration with smart home devices

## 🆘 Troubleshooting

### Common Issues

1. **ESP32 not connecting to WiFi**:

   - Check credentials
   - Verify network availability
   - Check signal strength

2. **UDP data not received**:

   - Verify server IP and port
   - Check firewall settings
   - Ensure both devices on same network

3. **Inaccurate current readings**:

   - Calibrate ACS712 sensor
   - Check connections
   - Verify voltage levels

4. **Frontend not loading**:
   - Check if backend is running
   - Verify CORS settings
   - Check browser console for errors

### Support

For issues and questions:

- Check the troubleshooting section
- Review the code comments
- Open an issue on GitHub

---

## ⚡ KSEB Tiered Pricing System

### **Smart Pricing for Kerala**

The system now includes KSEB's tiered pricing structure:

- **0-250 units**: ₹6.50/kWh
- **0-300 units**: ₹6.50/kWh
- **0-350 units**: ₹7.60/kWh
- **0-400 units**: ₹7.60/kWh
- **0-500 units**: ₹7.60/kWh
- **Above 500 units**: ₹8.70/kWh

### **Features**

- **Automatic slab detection** based on monthly consumption
- **Real-time cost calculation** using tiered rates
- **CSV configuration** for easy rate updates
- **Monthly consumption tracking** for accurate billing

### **CSV Configuration**

The system uses `backend/kseb_slabs.csv` for pricing configuration:

```csv
units_min,units_max,rate_per_kwh,slab_description,slab_type
0,250,6.50,0-250 units,domestic
0,300,6.50,0-300 units,domestic
0,350,7.60,0-350 units,domestic
0,400,7.60,0-400 units,domestic
0,500,7.60,0-500 units,domestic
500,999999,8.70,above 500 units,domestic
```

**Happy Carbon Tracking! 🌱**
