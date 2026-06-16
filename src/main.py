import argparse
import time
import logging
import random
import threading
from src.obfuscation.engine import ObfuscationEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def packet_receiver(pkt, is_dummy):
    """Callback to handle outgoing packets (e.g., send to network or log)."""
    type_str = "DUMMY" if is_dummy else "REAL "
    logging.info(f"SENT [{type_str}] Size={len(pkt)} bytes")

def user_traffic_simulator(engine):
    """Simulates a user sending messages."""
    messages = [
        b"Hello World",
        b"This is a secret message",
        b"Post-Quantum Cryptography is cool",
        b"Traffic Analysis Resistance",
        b"End of conversation"
    ]
    
    for msg in messages:
        delay = random.uniform(0.5, 3.0)
        time.sleep(delay)
        logging.info(f"USER: queuing message '{msg.decode()}'")
        engine.send_data(msg)

def main():
    parser = argparse.ArgumentParser(description="Post-Quantum Metadata Obfuscation Layer Demo")
    parser.add_argument("--duration", type=int, default=15, help="Duration to run the demo (seconds)")
    args = parser.parse_args()

    # Initialize Engine
    engine = ObfuscationEngine(output_callback=packet_receiver)
    
    # Start Engine
    engine.start()

    # Start User Simulation in a separate thread
    user_thread = threading.Thread(target=user_traffic_simulator, args=(engine,))
    user_thread.start()

    # Run for specified duration
    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        pass
    finally:
        engine.stop()
        user_thread.join()
        logging.info("Demo completed.")

if __name__ == "__main__":
    main()
