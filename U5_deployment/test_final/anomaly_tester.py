#!/usr/bin/env python3
"""
Anomaly Detection Interactive Tester with Handshake Protocol
Streams .h image files to MCU over USART1 and receives anomaly scores
with full ping-pong handshake to avoid bus conflicts
"""

import serial
import struct
import os
import re
import sys
import threading
import time
from pathlib import Path
import serial.tools.list_ports

# Protocol constants
PROTOCOL_START_MARKER = 0xAA
PROTOCOL_END_MARKER = 0xBB
MSG_TYPE_IMAGE_DATA = 0x01
MSG_TYPE_RESULT = 0x02

# Handshake markers
HANDSHAKE_INIT = 0xAA           # Python sends this to init
HANDSHAKE_CONFIRM = 0xBB        # MCU confirms with this + 0x00 0xCC 0xDD
IMAGE_RECEIVED_ACK = 0xDD       # MCU sends: 0xDD 0x01 0xBB 0xBB
READY_FOR_NEXT = 0xEE           # MCU sends: 0xEE 0x00 0xFF 0x00

ANOMALY_THRESHOLD = 0.5
IMAGE_SIZE = 150528  # 224 * 224 * 3


class AnomalyTester:
    def __init__(self, port='/dev/ttyACM0', baudrate=115200):
        """Initialize serial connection"""
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.monitor_thread = None
        self.monitor_running = True
        self.monitor_paused = False  # Flag to pause monitor during protocol
        self.connect()
    
    def connect(self):
        """Connect to MCU"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.5)
            print(f"[PYTHON] Connected to {self.port} at {self.baudrate} baud")
            # Clear any pending data
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            # Wait for MCU to boot
            print("[PYTHON] Waiting for MCU to boot and initialize...")
            time.sleep(2)  # Give MCU time to boot
            
            # Start background thread to monitor MCU output
            self.monitor_thread = threading.Thread(target=self._monitor_mcu_output, daemon=True)
            self.monitor_thread.start()
            
            time.sleep(0.5)  # Let monitoring start
            
        except serial.SerialException as e:
            print(f"[PYTHON] ERROR: Failed to connect to {self.port}: {e}")
            print("\n[PYTHON] Available COM ports:")
            ports = serial.tools.list_ports.comports()
            if ports:
                for port in ports:
                    print(f"  - {port.device}: {port.description}")
            else:
                print("  No COM ports found!")
            sys.exit(1)
    
    def _monitor_mcu_output(self):
        """Background thread to continuously read and display MCU output"""
        buffer = ""
        while self.monitor_running:
            try:
                # CRITICAL: Only read if NOT paused (check twice for safety)
                if self.monitor_paused:
                    time.sleep(0.02)
                    continue
                
                # Double-check pause flag before reading
                if not self.monitor_paused and self.ser and self.ser.in_waiting > 0:
                    # Read only 1 byte at a time to be less intrusive
                    data = self.ser.read(1)
                    if data:
                        try:
                            text = data.decode('utf-8', errors='replace')
                            buffer += text
                            
                            # Print complete lines
                            while '\n' in buffer:
                                line, buffer = buffer.split('\n', 1)
                                if line.strip():
                                    print(f"[MCU] {line}")
                        except:
                            pass
                time.sleep(0.02)
            except:
                break
    
    def close(self):
        """Close serial connection"""
        self.monitor_running = False
        time.sleep(0.1)
        if self.ser:
            self.ser.close()
    
    def crc16(self, data):
        """Calculate CRC16 (CCITT)"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                crc &= 0xFFFF
        return crc
    
    def parse_h_file(self, filepath):
        """Parse .h file and extract image data as bytes"""
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Find the array definition
        match = re.search(r'= \{([^}]+)\}', content, re.DOTALL)
        if not match:
            raise ValueError(f"Could not find array data in {filepath}")
        
        array_str = match.group(1)
        
        # Extract all hex values (0x??)
        hex_values = re.findall(r'0x([0-9a-fA-F]{2})', array_str)
        
        if not hex_values:
            raise ValueError(f"Could not find hex values in {filepath}")
        
        # Convert to bytes
        image_data = bytes(int(h, 16) for h in hex_values)
        
        if len(image_data) != IMAGE_SIZE:
            raise ValueError(f"Image size mismatch: got {len(image_data)}, expected {IMAGE_SIZE}")
        
        return image_data
    
    def wait_for_mcu_boot(self):
        """Wait indefinitely for MCU to send initial ready signal
        This blocks until user resets MCU and it boots"""
        print("\n[PYTHON STARTUP] ========================================")
        print("[PYTHON STARTUP] === WAITING FOR MCU BOOT ===")
        print("[PYTHON STARTUP] Waiting for MCU ready signal...")
        print("[PYTHON STARTUP] >>> PRESS MCU RESET NOW <<<")
        print("[PYTHON STARTUP] ========================================\n")
        
        # CRITICAL: Pause monitor so it does not consume protocol bytes
        self.monitor_paused = True
        time.sleep(0.3)

        try:
            # Scan stream for the exact ready sequence, ignore any text
            expected = [READY_FOR_NEXT, 0x00, 0xFF, 0x00]
            match_idx = 0
            start_time = time.time()

            while True:  # NO TIMEOUT - wait forever
                if self.ser.in_waiting > 0:
                    byte = self.ser.read(1)
                    if not byte:
                        continue
                    bval = byte[0]
                    if bval == expected[match_idx]:
                        match_idx += 1
                        if match_idx == len(expected):
                            elapsed = time.time() - start_time
                            print(f"\n[PYTHON STARTUP] ✓✓✓ MCU READY! ({elapsed:.2f}s)")
                            print("[PYTHON STARTUP] ========================================\n")
                            time.sleep(0.1)
                            return True
                    else:
                        match_idx = 1 if bval == expected[0] else 0
                else:
                    time.sleep(0.05)
        finally:
            time.sleep(0.2)
            self.monitor_paused = False
    
    def handshake_with_mcu(self):
        """Perform handshake with MCU before sending image - WAITS indefinitely for MCU"""
        print("\n[PYTHON HANDSHAKE] ========================================")
        print("[PYTHON HANDSHAKE] === WAITING FOR MCU HANDSHAKE ===")
        print("[PYTHON HANDSHAKE] Sending init signal (0xAA)...")
        print("[PYTHON HANDSHAKE] >>> THIS WILL BLOCK UNTIL MCU RESPONDS <<<")
        print("[PYTHON HANDSHAKE] ========================================\n")
        
        # CRITICAL: Pause monitor thread to avoid consuming protocol bytes
        self.monitor_paused = True
        time.sleep(0.3)  # MUST give monitor time to stop
        
        try:
            # Clear any stray characters in the input buffer
            self.ser.reset_input_buffer()
            time.sleep(0.1)
            
            # Clear buffers
            self.ser.reset_output_buffer()
            time.sleep(0.05)
            
            # Send init marker (0xAA)
            self.ser.write(bytes([HANDSHAKE_INIT]))
            self.ser.flush()
            time.sleep(0.05)  # Small delay for MCU to process and respond
            
            # Wait INDEFINITELY for response 0xBB 0x00 0xCC 0xDD - READ BYTE BY BYTE
            print("[PYTHON HANDSHAKE] Waiting for response (0xBB 0x00 0xCC 0xDD)...")
            
            response = []
            timeout_count = 0
            start_time = time.time()
            
            while len(response) < 4:  # Read exactly 4 bytes
                if self.ser.in_waiting > 0:
                    byte = self.ser.read(1)
                    if byte:
                        response.append(byte[0])
                        print(f"[PYTHON HANDSHAKE] Byte {len(response)}: 0x{byte[0]:02X}")
                        timeout_count = 0
                else:
                    time.sleep(0.05)
                    timeout_count += 1
                    if timeout_count % 20 == 0:  # Print every 1 second
                        elapsed = time.time() - start_time
                        print(f"[PYTHON HANDSHAKE] Still waiting... ({elapsed:.0f}s elapsed)")
            
            # Verify the response
            expected = [HANDSHAKE_CONFIRM, 0x00, 0xCC, 0xDD]
            if response == expected:
                elapsed = time.time() - start_time
                print(f"\n[PYTHON HANDSHAKE] ✓✓✓ HANDSHAKE SUCCESS! ({elapsed:.2f}s)")
                print("[PYTHON HANDSHAKE] ========================================\n")
                time.sleep(0.1)  # Stabilization
                return True
            else:
                print(f"\n[PYTHON HANDSHAKE] ✗✗✗ ERROR! Got: {' '.join(f'0x{b:02X}' for b in response)}")
                print(f"[PYTHON HANDSHAKE] Expected: {' '.join(f'0x{b:02X}' for b in expected)}")
                return False
                
        finally:
            # CRITICAL: Resume monitor thread
            time.sleep(0.2)
            self.monitor_paused = False
    
    def send_image(self, image_data):
        """Send image to MCU using protocol - WAITS for ACK indefinitely"""
        if len(image_data) != IMAGE_SIZE:
            print(f"[PYTHON SEND] ERROR: Invalid image size {len(image_data)}")
            return False
        
        # CRITICAL: Pause monitor thread to avoid consuming protocol bytes
        self.monitor_paused = True
        time.sleep(0.3)  # MUST give monitor time to stop
        
        try:
            print(f"\n[PYTHON SEND] ========================================")
            print(f"[PYTHON SEND] === SENDING IMAGE ({len(image_data)} bytes) ===")
            
            # Build message: [START] [TYPE] [SIZE_4BYTES] [DATA] [CRC] [END]
            message = bytearray()
            message.append(PROTOCOL_START_MARKER)
            message.append(MSG_TYPE_IMAGE_DATA)
            message.extend(struct.pack('<I', len(image_data)))  # Size (little-endian)
            message.extend(image_data)
            
            # Calculate CRC on image payload only (matches MCU implementation)
            crc_data = image_data
            crc = self.crc16(crc_data)
            message.extend(struct.pack('<H', crc))  # CRC (little-endian)
            message.append(PROTOCOL_END_MARKER)
            
            # Clear buffers
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            time.sleep(0.05)
            
            # Send
            print(f"[PYTHON SEND] Transmitting {len(message)} bytes...")
            bytes_sent = self.ser.write(bytes(message))
            self.ser.flush()
            print(f"[PYTHON SEND] Sent {bytes_sent} bytes")
            time.sleep(0.1)
            
            # Wait INDEFINITELY for image received ACK - READ BYTE BY BYTE
            print("[PYTHON SEND] >>> WAITING FOR MCU ACK (0xDD 0x01 0xBB 0xBB) <<<")
            
            expected = [IMAGE_RECEIVED_ACK, 0x01, 0xBB, 0xBB]
            match_idx = 0
            timeout_count = 0
            start_time = time.time()

            while True:  # Scan until the exact ACK sequence is found
                if self.ser.in_waiting > 0:
                    byte = self.ser.read(1)
                    if not byte:
                        continue
                    bval = byte[0]
                    if bval == expected[match_idx]:
                        match_idx += 1
                        print(f"[PYTHON SEND] ACK byte {match_idx}: 0x{bval:02X}")
                        if match_idx == len(expected):
                            elapsed = time.time() - start_time
                            print(f"\n[PYTHON SEND] ✓✓✓ IMAGE ACK SUCCESS! ({elapsed:.2f}s)")
                            print("[PYTHON SEND] ========================================\n")
                            time.sleep(0.1)
                            return True
                    else:
                        match_idx = 1 if bval == expected[0] else 0
                else:
                    time.sleep(0.05)
                    timeout_count += 1
                    if timeout_count % 20 == 0:  # Print every 1 second
                        elapsed = time.time() - start_time
                        print(f"[PYTHON SEND] Still waiting for ACK... ({elapsed:.0f}s elapsed)")
                
        except serial.SerialException as e:
            print(f"[PYTHON SEND] ERROR: {e}")
            return False
        finally:
            # CRITICAL: Resume monitor thread
            time.sleep(0.2)
            self.monitor_paused = False
    
    def receive_result(self):
        """Receive anomaly score from MCU - WAITS indefinitely for result"""
        print("\n[PYTHON RECV] ========================================")
        print("[PYTHON RECV] === WAITING FOR RESULT ===")
        
        # CRITICAL: Pause monitor thread to avoid consuming protocol bytes
        self.monitor_paused = True
        time.sleep(0.3)  # MUST give monitor time to stop
        
        try:
            print("[PYTHON RECV] Searching for result marker (0xAA)...")
            print("[PYTHON RECV] >>> WAITING FOR MCU PROCESSING (BLOCKING) <<<")
            
            # Scan for the binary start marker (0xAA)
            marker_found = False
            start_time = time.time()
            bytes_searched = 0
            
            while not marker_found:
                if self.ser.in_waiting > 0:
                    byte = self.ser.read(1)
                    bytes_searched += 1
                    
                    if byte[0] == PROTOCOL_START_MARKER:
                        elapsed = time.time() - start_time
                        print(f"\n[PYTHON RECV] ✓ Found result marker (0xAA) after {bytes_searched} bytes ({elapsed:.1f}s)")
                        marker_found = True
                        break
                else:
                    time.sleep(0.05)
            
            # Now read the rest of the message byte by byte
            msg_type = self.ser.read(1)
            if not msg_type or msg_type[0] != MSG_TYPE_RESULT:
                print(f"[PYTHON RECV] ✗ ERROR: Invalid message type 0x{msg_type[0]:02X if msg_type else 'FF'}")
                return None
            
            anomaly_b = self.ser.read(4)
            if len(anomaly_b) != 4:
                print(f"[PYTHON RECV] ✗ ERROR: Failed to read anomaly score")
                return None
            anomaly_int = struct.unpack('<i', anomaly_b)[0]
            anomaly_score = anomaly_int / 10000.0
            
            status = self.ser.read(1)
            if not status:
                print(f"[PYTHON RECV] ✗ ERROR: Failed to read status")
                return None
            is_anomaly = status[0]
            
            crc_b = self.ser.read(2)
            if len(crc_b) != 2:
                print(f"[PYTHON RECV] ✗ ERROR: Failed to read CRC")
                return None
            received_crc = struct.unpack('<H', crc_b)[0]
            
            end = self.ser.read(1)
            if not end or end[0] != PROTOCOL_END_MARKER:
                print(f"[PYTHON RECV] ✗ ERROR: Invalid end marker 0x{end[0]:02X if end else 'FF'}")
                return None
            
            # Verify CRC
            crc_data = msg_type + anomaly_b + status
            calculated_crc = self.crc16(crc_data)
            
            if received_crc != calculated_crc:
                print(f"[PYTHON RECV] ✗ ERROR: CRC mismatch! Got 0x{received_crc:04X}, expected 0x{calculated_crc:04X}")
                return None
            
            print(f"[PYTHON RECV] Anomaly score: {anomaly_score:.4f} ({'ANOMALY' if is_anomaly else 'NORMAL'})")
            print("[PYTHON RECV] ✓✓✓ RESULT RECEIVED AND VALIDATED!")
            print("[PYTHON RECV] ========================================\n")
            
            return {
                'score': anomaly_score,
                'is_anomaly': bool(is_anomaly),
                'threshold': ANOMALY_THRESHOLD
            }
        
        except serial.SerialException as e:
            print(f"[PYTHON RECV] ERROR: {e}")
            return None
        finally:
            # CRITICAL: Resume monitor thread
            time.sleep(0.2)
            self.monitor_paused = False
    
    def wait_for_ready_signal(self):
        """Wait INDEFINITELY for MCU to send ready_for_next signal"""
        print("[PYTHON READY] ========================================")
        print("[PYTHON READY] === WAITING FOR READY SIGNAL ===")
        print("[PYTHON READY] >>> WAITING FOR MCU (0xEE 0x00 0xFF 0x00) <<<")
        
        # CRITICAL: Pause monitor thread to avoid consuming protocol bytes
        self.monitor_paused = True
        time.sleep(0.3)  # MUST give monitor time to stop
        
        try:
            # Scan stream for the exact ready sequence, do not clear buffers
            expected = [READY_FOR_NEXT, 0x00, 0xFF, 0x00]
            match_idx = 0
            timeout_count = 0
            start_time = time.time()

            while True:  # Wait indefinitely
                if self.ser.in_waiting > 0:
                    byte = self.ser.read(1)
                    if not byte:
                        continue
                    bval = byte[0]
                    if bval == expected[match_idx]:
                        match_idx += 1
                        print(f"[PYTHON READY] Ready byte {match_idx}: 0x{bval:02X}")
                        if match_idx == len(expected):
                            elapsed = time.time() - start_time
                            print(f"\n[PYTHON READY] ✓✓✓ READY SIGNAL RECEIVED! ({elapsed:.2f}s)")
                            print("[PYTHON READY] ========================================\n")
                            time.sleep(0.1)
                            return True
                    else:
                        match_idx = 1 if bval == expected[0] else 0
                else:
                    time.sleep(0.05)
                    timeout_count += 1
                    if timeout_count % 20 == 0:  # Print every 1 second
                        elapsed = time.time() - start_time
                        print(f"[PYTHON READY] Still waiting... ({elapsed:.0f}s elapsed)")
        finally:
            # CRITICAL: Resume monitor thread
            time.sleep(0.2)
            self.monitor_paused = False
    
    def find_h_files(self, directory='/mnt/c/Users/Faebe/Desktop/onnx_models/dataset/tinyglass_mmdataset/headers'):
        """Find all .h image files in directory"""
        h_files = []
        path = Path(directory)
        for file in sorted(path.glob('*.h')):
            if 'test_image' not in file.name:  # Skip the template
                h_files.append(file)
        return h_files


def main():
    # Configuration
    PORT = '/dev/ttyACM0'  # WSL: /dev/ttyACM1, Windows: COM10
    DIRECTORY = '/mnt/c/Users/Faebe/Desktop/onnx_models/dataset/tinyglass_mmdataset/headers'  # Directory containing .h files
    
    # Allow command-line override
    if len(sys.argv) > 1:
        PORT = sys.argv[1]
    
    print(f"\n{'='*70}")
    print(f"ANOMALY DETECTION INTERACTIVE TESTER (with handshake)")
    print(f"{'='*70}")
    print(f"Port: {PORT}")
    print(f"Directory: {DIRECTORY}\n")

    # Create tester
    tester = AnomalyTester(port=PORT)
    
    # Wait for MCU to boot
    tester.wait_for_mcu_boot()
    
    # Find image files
    image_files = tester.find_h_files(DIRECTORY)
    
    if not image_files:
        print(f"[PYTHON] ERROR: No image files found in {DIRECTORY}")
        tester.close()
        sys.exit(1)
    
    print(f"[PYTHON] Found {len(image_files)} image files:")
    for i, f in enumerate(image_files, 1):
        print(f"[PYTHON]   {i}. {f.name}")
    print()
    
    # Process each image
    results = []
    for i, img_file in enumerate(image_files, 1):
        print(f"\n{'='*70}")
        print(f"Image {i}/{len(image_files)}: {img_file.name}")
        print(f"{'='*70}")
        
        # Parse image file
        try:
            print(f"[PYTHON] Parsing {img_file.name}...", end='', flush=True)
            image_data = tester.parse_h_file(img_file)
            print(f" OK ({len(image_data)} bytes)")
        except Exception as e:
            print(f" ERROR: {e}")
            continue
        
        # === HANDSHAKE === (waits indefinitely)
        tester.handshake_with_mcu()
        
        # === SEND IMAGE === (waits indefinitely for ACK)
        if not tester.send_image(image_data):
            print("[PYTHON] CRITICAL ERROR: Send failed, stopping")
            break
        
        # === RECEIVE RESULT === (waits indefinitely)
        result = tester.receive_result()
        
        if result:
            # Display result
            score_str = f"{result['score']:.4f}"
            status = "ANOMALY" if result['is_anomaly'] else "NORMAL"
            print(f"\n[PYTHON] Result: Score={score_str}, Status={status}")
            results.append({
                'file': img_file.name,
                'score': result['score'],
                'is_anomaly': result['is_anomaly']
            })
        else:
            print("[PYTHON] ERROR: No result received")
        
        # === WAIT FOR READY SIGNAL === (waits indefinitely)
        tester.wait_for_ready_signal()
        
        # Wait for user to press Enter before next image
        # if i < len(image_files):
        #    input("\n[PYTHON] Press Enter to test next image...")
    
    # Summary
    print(f"\n\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"{'Filename':<40} {'Score':<12} {'Status':<12}")
    print("-" * 70)
    
    for r in results:
        score_str = f"{r['score']:.4f}"
        status = "ANOMALY" if r['is_anomaly'] else "NORMAL"
        print(f"{r['file']:<40} {score_str:<12} {status:<12}")
    
    # Close
    tester.close()
    print("\n[PYTHON] Done!")


if __name__ == '__main__':
    main()
