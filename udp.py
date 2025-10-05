import socket

# --- Configuration ---
# This port MUST match the udpPort in your ESP32 code
UDP_PORT = 4210  
# Listen on all available network interfaces ("0.0.0.0")
UDP_IP = "0.0.0.0" 

# Create a UDP socket
# socket.AF_INET means we are using IPv4
# socket.SOCK_DGRAM means it's a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the IP and port to listen for incoming data
sock.bind((UDP_IP, UDP_PORT))

print(f"✅ UDP listener started on port {UDP_PORT}...")
print("Waiting to receive data from the ESP32. Press Ctrl+C to exit.")

try:
    while True:
        # Wait for a packet to be received (buffer size is 1024 bytes)
        data, addr = sock.recvfrom(1024) 
        
        # Decode the received bytes into a string
        message = data.decode('utf-8')
        
        # The data from the Arduino is "Current,Power,Energy,Cost"
        # Split the string by the comma to get individual values
        values = message.split(',')
        
        # Make sure the received message has the correct number of parts
        if len(values) == 4:
            # Print the data in a nice format
            print(f"Received from {addr[0]}: \t"
                  f"Current: {values[0]} A | "
                  f"Power: {values[1]} W | "
                  f"Energy: {values[2]} Wh | "
                  f"Cost: ${values[3]}")
        else:
            print(f"Received malformed packet from {addr[0]}: {message}")

except KeyboardInterrupt:
    print("\nListener stopped.")
    sock.close()