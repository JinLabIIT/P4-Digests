import socket
import time
import argparse
import sys
import json

bus_data = {
    "B1": {"voltage": 1.02, "phaseAngle": -5.3},
    "B2": {"voltage": 0.98, "phaseAngle": -6.1},
    "B3": {"voltage": 1.00, "phaseAngle": -5.8},
    "B4": {"voltage": 1.01, "phaseAngle": 0.5},
    "B5": {"voltage": 0.99, "phaseAngle": 0.2},
    "B6": {"voltage": 1.02, "phaseAngle": -5.3},
    "B7": {"voltage": 0.98, "phaseAngle": -6.1},
    "B8": {"voltage": 1.00, "phaseAngle": -5.8},
    "B9": {"voltage": 1.01, "phaseAngle": 0.5},
    "B10": {"voltage": 0.99, "phaseAngle": 0.2},
    "B11": {"voltage": 1.02, "phaseAngle": -5.3},
    "B12": {"voltage": 0.98, "phaseAngle": -6.1},
    "B13": {"voltage": 1.00, "phaseAngle": -5.8},
    "B14": {"voltage": 1.01, "phaseAngle": 0.5},
    "B15": {"voltage": 0.99, "phaseAngle": 0.2},
    "B16": {"voltage": 1.02, "phaseAngle": -5.3},
    "B17": {"voltage": 0.98, "phaseAngle": -6.1},
    "B18": {"voltage": 1.00, "phaseAngle": -5.8},
    "B19": {"voltage": 1.01, "phaseAngle": 0.5},
    "B20": {"voltage": 0.99, "phaseAngle": 0.2},
    "B21": {"voltage": 1.02, "phaseAngle": -5.3},
    "B22": {"voltage": 0.98, "phaseAngle": -6.1},
    "B23": {"voltage": 1.00, "phaseAngle": -5.8},
    "B24": {"voltage": 1.01, "phaseAngle": 0.5},
    "B25": {"voltage": 0.99, "phaseAngle": 0.2},
    "B26": {"voltage": 1.02, "phaseAngle": -5.3},
    "B27": {"voltage": 0.98, "phaseAngle": -6.1},
    "B28": {"voltage": 1.00, "phaseAngle": -5.8},
    "B29": {"voltage": 1.01, "phaseAngle": 0.5},
    "B30": {"voltage": 0.99, "phaseAngle": 0.2},
}

def load_config(config_file):
    """Loads the JSON configuration file."""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at '{config_file}'", file=sys.stderr)
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{config_file}'", file=sys.stderr)
        return None

def pmu_send(pdc_ip, pdc_port, bus_ids, interval):
    """
    :param pdc_ip: The IP address of the PDC (destination).
    :param pdc_port: The port number of the PDC.
    :param bus_ids: A list of bus IDs this PMU instance should monitor.
    :param interval: The time to wait between sending each batch of measurements.
    """
    pmu_socket = None
    print(f"--- PMU Started for Buses: {', '.join(bus_ids)} ---")
    print(f"Attempting to connect to PDC at {pdc_ip}:{pdc_port}...")

    try:
        # Create a TCP/IP socket
        pmu_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Connect the socket to the server's address and port
        pmu_socket.connect((pdc_ip, pdc_port))
        print("Connection to PDC established successfully.")

        while True:
            # Iterate through each bus this PMU is responsible for
            for bus_id in bus_ids:
                if bus_id not in bus_data:
                    print(f"Warning: Bus ID '{bus_id}' not found in database. Skipping.", file=sys.stderr)
                    continue

                # Get the static data for the current bus
                bus_data = bus_data[bus_id]
                voltage = bus_data["voltage"]
                angle = bus_data["phaseAngle"]
                timestamp = time.time()

                # Format the data string as requested
                message = f"busID: {bus_id} voltage: {voltage} phaseAngle: {angle} timestamp: {timestamp}\n"
                
                # Send the data, encoded as bytes
                pmu_socket.sendall(message.encode('utf-8'))
                print(f"Sent data for {bus_id}")
            
            #print(f"--- Batch complete. Waiting for {interval} second(s)... ---") #use for debugging
            time.sleep(interval)

    except ConnectionRefusedError:
        print(f"Error: Connection refused. Is the PDC server running on {pdc_ip}:{pdc_port}?", file=sys.stderr)
    except KeyboardInterrupt:
        print("\n--- PMU Stopped by user ---")
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
    finally:
        # Ensure the socket is closed on exit or error
        if pmu_socket:
            print("Closing connection to PDC.")
            pmu_socket.close()

if __name__ == "__main__":

    config = load_config('pmu_config.json')
    if config is None:
        sys.exit(1)

    global_config = config.get("global_settings", {})
    hostname = socket.gethostname()
    
    host_config = config.get(hostname, config.get('default', {}))
    
    default_ip = host_config.get('pdc_ip', global_config.get('pdc_ip'))
    default_port = host_config.get('pdc_port', global_config.get('pdc_port'))
    default_buses = host_config.get('buses', global_config.get('buses', []))
    default_interval = host_config.get('interval', global_config.get('interval'))

    parser = argparse.ArgumentParser(description="PMU")
    
    parser.add_argument('--ip', type=str, default=default_ip,
                        help=f"PDC IP address. (default for this host: {default_ip})")
    
    parser.add_argument('--port', type=int, default=default_port,
                        help=f"PDC port number. (default for this host: {default_port})")
    
    parser.add_argument('--buses', type=str, default=','.join(default_buses),
                        help=f"Comma-separated list of Bus IDs. (default for this host: {','.join(default_buses)})")
    
    parser.add_argument('--interval', type=float, default=default_interval,
                        help=f"Sending interval. (default for this host: {default_interval})")

    args = parser.parse_args()
    
    # Final check to ensure all settings have a value.
    if not all([args.ip, args.port, args.buses, args.interval is not None]):
        print("Error: A required setting is missing.", file=sys.stderr)
        print("Please provide it via command-line or in pmu_config.json (host-specific or global).", file=sys.stderr)
        sys.exit(1)

    buses_to_monitor = args.buses.split(',')
    pmu_send(args.ip, args.port, buses_to_monitor, args.interval)