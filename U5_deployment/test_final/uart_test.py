#!/usr/bin/env python3
"""
Simple test to verify UART communication works
"""

import serial
import time

def test_uart(port='/dev/ttyACM0'):
    try:
        # Open serial port
        ser = serial.Serial(port, 115200, timeout=1)
        print(f"Connected to {port}")
        
        # Clear any pending data
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.5)
        
        # Read any initial output from MCU
        print("\n--- Initial MCU output ---")
        while ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            print(data.decode('utf-8', errors='ignore'), end='')
        
        # Test 1: Send a simple byte and see if MCU responds
        print("\n\n--- Test 1: Sending start marker (0xAA) ---")
        ser.write(bytes([0xAA]))
        print("Sent: 0xAA")
        time.sleep(0.5)
        
        # Read response
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            print(f"MCU response ({len(data)} bytes):")
            print(data.decode('utf-8', errors='ignore'))
        else:
            print("No response from MCU")
        
        # Test 2: Send message type
        print("\n--- Test 2: Sending message type (0x01) ---")
        ser.write(bytes([0x01]))
        print("Sent: 0x01")
        time.sleep(0.5)
        
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            print(f"MCU response ({len(data)} bytes):")
            print(data.decode('utf-8', errors='ignore'))
        else:
            print("No response from MCU")
        
        ser.close()
        
    except serial.SerialException as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    test_uart()
