import socket
import json
import threading
import sqlite3
from datetime import datetime
import time

class UDPServer:
    def __init__(self, host='0.0.0.0', port=8888, db_path='carbon_footprint.db'):
        self.host = host
        self.port = port
        self.db_path = db_path
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = False
        
    def start(self):
        """Start the UDP server"""
        try:
            self.socket.bind((self.host, self.port))
            self.running = True
            print(f"UDP Server started on {self.host}:{self.port}")
            
            while self.running:
                try:
                    data, addr = self.socket.recvfrom(1024)
                    self.handle_data(data, addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error receiving data: {e}")
                    
        except Exception as e:
            print(f"Failed to start UDP server: {e}")
        finally:
            self.socket.close()
    
    def stop(self):
        """Stop the UDP server"""
        self.running = False
        self.socket.close()
    
    def handle_data(self, data, addr):
        """Handle incoming IoT data"""
        try:
            # Parse JSON data from ESP32
            message = json.loads(data.decode('utf-8'))
            print(f"Received from {addr}: {message}")
            
            # Process different types of IoT data
            if message.get('type') == 'energy':
                self.process_energy_data(message)
            elif message.get('type') == 'commute':
                self.process_commute_data(message)
            else:
                print(f"Unknown message type: {message.get('type')}")
                
        except json.JSONDecodeError as e:
            print(f"Invalid JSON from {addr}: {e}")
        except Exception as e:
            print(f"Error processing data from {addr}: {e}")
    
    def process_energy_data(self, data):
        """Process energy consumption data from IoT sensors"""
        try:
            # Extract data from IoT message
            power_watts = data.get('power_watts', 0)
            duration_hours = data.get('duration_hours', 0)
            device_id = data.get('device_id', 'unknown')
            timestamp = data.get('timestamp', datetime.now().isoformat())
            
            # Calculate energy consumption
            energy_kwh = (power_watts * duration_hours) / 1000
            
            # Calculate CO2 emissions (kg CO2/kWh)
            co2_emissions = energy_kwh * 0.5  # Adjust based on your region's grid mix
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO energy_consumption 
                (date, power_consumption_watts, duration_hours, energy_kwh, co2_emissions_kg)
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp.split('T')[0], power_watts, duration_hours, energy_kwh, co2_emissions))
            
            conn.commit()
            conn.close()
            
            print(f"Energy data stored: {energy_kwh:.3f} kWh, {co2_emissions:.3f} kg CO2")
            
        except Exception as e:
            print(f"Error processing energy data: {e}")
    
    def process_commute_data(self, data):
        """Process commute data from IoT devices (e.g., GPS tracking)"""
        try:
            # Extract data from IoT message
            distance_km = data.get('distance_km', 0)
            transport_mode = data.get('transport_mode', 'car')
            device_id = data.get('device_id', 'unknown')
            timestamp = data.get('timestamp', datetime.now().isoformat())
            
            # Calculate CO2 emissions
            emission_factors = {
                "car": 0.192,
                "motorcycle": 0.103,
                "bus": 0.089,
                "train": 0.041,
                "bicycle": 0.0,
                "walking": 0.0,
                "electric_car": 0.053,
                "hybrid_car": 0.120
            }
            
            co2_emissions = distance_km * emission_factors.get(transport_mode.lower(), 0.1)
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO commute_logs 
                (date, transport_mode, distance_km, co2_emissions_kg)
                VALUES (?, ?, ?, ?)
            """, (timestamp.split('T')[0], transport_mode, distance_km, co2_emissions))
            
            conn.commit()
            conn.close()
            
            print(f"Commute data stored: {distance_km} km, {co2_emissions:.3f} kg CO2")
            
        except Exception as e:
            print(f"Error processing commute data: {e}")

def start_udp_server():
    """Start the UDP server in a separate thread"""
    server = UDPServer()
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    return server

if __name__ == "__main__":
    # Run UDP server standalone
    server = UDPServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("Stopping UDP server...")
        server.stop()
