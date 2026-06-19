#!/usr/bin/env python3
"""
Simple serial port monitor to see what the MCU is actually sending
"""

import serial
import sys
import time

def monitor_serial(port='/dev/ttyACM0', baudrate=115200):
    try:
        ser = serial.Serial(port, baudrate, timeout=0.1)
        print(f"Connected to {port} at {baudrate} baud")
        print("Reading data (press Ctrl+C to exit)...\n")
        
        # Clear buffer
        ser.reset_input_buffer()
        
        # Monitor for 30 seconds
        start_time = time.time()
        total_bytes = 0
        
        while time.time() - start_time < 30:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                total_bytes += len(data)
                try:
                    text = data.decode('utf-8', errors='replace')
                    print(text, end='', flush=True)
                except:
                    print(f"[{len(data)} bytes of binary data]", flush=True)
        
        print(f"\n\nTotal bytes received: {total_bytes}")
        
        if total_bytes == 0:
            print("ERROR: No data received from MCU!")
            print("Check that:")
            print("  1. MCU is powered on")
            print("  2. MCU is flashed with the latest code")
            print("  3. USB cable is connected properly")
            print("  4. Port /dev/ttyACM0 is correct")
        else:
            print("MCU is responding - continue with anomaly_tester.py")
        
        ser.close()
        
    except serial.SerialException as e:
        print(f"ERROR: Failed to open {port}: {e}")
        sys.exit(1)

if __name__ == '__main__':
    monitor_serial()
