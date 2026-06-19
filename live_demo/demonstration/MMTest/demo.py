#!/usr/bin/env python3

import serial
import struct
import re
import time
from pathlib import Path

# NEW
from PIL import Image, ImageDraw, ImageFont
import os

# =========================
# SETTINGS
# =========================
PORT = "COM5"
FOLDER = r"C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\headers"
PIC_FOLDER = r"C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\cropped"
RESULT_FOLDER = r"C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\results"

Path(RESULT_FOLDER).mkdir(exist_ok=True, parents=True)

BAUDRATE = 3000000
THRESHOLD = 0.12

PROTOCOL_START_MARKER = 0xAA
PROTOCOL_END_MARKER   = 0xBB

MSG_TYPE_IMAGE_DATA = 0x01
MSG_TYPE_RESULT     = 0x02

IMAGE_SIZE = 224 * 224 * 3


class MCU:

    def __init__(self):
        self.ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)
        time.sleep(2)

        # DO NOT flush blindly at 3Mbps (causes race conditions)
        self.ser.reset_input_buffer()

    # =========================
    # IMAGE LOADING
    # =========================
    def load_image(self, path):
        text = Path(path).read_text()
        vals = re.findall(r'0x([0-9a-fA-F]{2})', text)
        data = bytes(int(v, 16) for v in vals)

        if len(data) != IMAGE_SIZE:
            raise ValueError(f"Bad image size: {len(data)}")

        return data

    # =========================
    # CRC
    # =========================
    def crc16(self, data):
        crc = 0xFFFF
        for b in data:
            crc ^= (b << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
                crc &= 0xFFFF
        return crc

    # =========================
    # SEND IMAGE
    # =========================
    def send_image(self, image_data):

        msg = bytearray()
        msg.append(PROTOCOL_START_MARKER)
        msg.append(MSG_TYPE_IMAGE_DATA)

        msg.extend(struct.pack("<I", len(image_data)))
        msg.extend(image_data)

        crc = self.crc16(image_data)
        msg.extend(struct.pack("<H", crc))

        msg.append(PROTOCOL_END_MARKER)

        self.ser.write(msg)
        self.ser.flush()

    # =========================
    # SAFE READ (WITH TIMEOUT)
    # =========================
    def read_exact(self, n, timeout=2.0):
        data = bytearray()
        start = time.time()

        while len(data) < n:
            if time.time() - start > timeout:
                raise TimeoutError(f"Timeout waiting for {n} bytes")

            chunk = self.ser.read(n - len(data))
            if chunk:
                data.extend(chunk)

        return data

    # =========================
    # SYNC TO START MARKER
    # =========================
    def sync_to_start(self, timeout=5.0):

        start = time.time()
        buffer = bytearray()

        while True:

            if time.time() - start > timeout:
                raise TimeoutError("No start marker received")

            chunk = self.ser.read(1)

            if chunk:
                buffer.append(chunk[0])

                if PROTOCOL_START_MARKER in buffer:
                    return

    # =========================
    # RECEIVE RESULT (FIXED + SAFE)
    # =========================
    def receive_result(self):

        self.sync_to_start()

        msg_type = self.read_exact(1)[0]

        if msg_type != MSG_TYPE_RESULT:
            print(f"[ERROR] Bad msg type: {msg_type}")
            return None

        anomaly_bytes = self.read_exact(4)
        status_byte   = self.read_exact(1)

        score = struct.unpack("<i", anomaly_bytes)[0] / 10000.0
        is_anomaly = score <= THRESHOLD

        inference_us = struct.unpack("<I", self.read_exact(4))[0]
        anomaly_us   = struct.unpack("<I", self.read_exact(4))[0]
        loading_us   = struct.unpack("<I", self.read_exact(4))[0]

        crc_received = struct.unpack("<H", self.read_exact(2))[0]

        crc_data = (
            bytes([msg_type]) +
            anomaly_bytes +
            status_byte +
            struct.pack("<I", inference_us) +
            struct.pack("<I", anomaly_us) +
            struct.pack("<I", loading_us)
        )

        crc_calc = self.crc16(crc_data)

        if crc_calc != crc_received:
            print(f"[CRC ERROR] got={crc_received:04X} expected={crc_calc:04X}")
            return None

        end = self.read_exact(1)[0]

        if end != PROTOCOL_END_MARKER:
            print(f"[ERROR] Bad end marker: {end:02X}")
            return None

        return is_anomaly, score

    # =========================
    # NEW: FIND IMAGE FILE
    # =========================
    def find_image(self, base_name):
        for ext in [".jpg", ".jpeg", ".png", ".bmp"]:
            path = Path(PIC_FOLDER) / f"{base_name}{ext}"
            if path.exists():
                return path
        return None

    # =========================
    # NEW: SAVE ANNOTATED IMAGE
    # =========================
    def save_result_image(self, base_name, score, is_anomaly):

        img_path = self.find_image(base_name)

        if img_path is None:
            print(f"[WARN] No image found for {base_name}")
            return

        img = Image.open(img_path).convert("RGB")
        draw = ImageDraw.Draw(img)

        w, h = img.size  # <-- use image size for consistency

        color = (255, 0, 0) if is_anomaly else (0, 200, 0)
        label = f"{'ANOMALY' if is_anomaly else 'NORMAL'}  score={score:.6f}"

        # =========================
        # CONSISTENT SCALING
        # =========================
        font_size = max(16, int(h * 0.05))   # 5% of image height
        padding   = max(6, int(font_size * 0.4))

        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), label, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x0, y0 = 10, 10
        x1 = x0 + text_w + padding * 2
        y1 = y0 + text_h + padding * 2

        # background box
        draw.rectangle([x0, y0, x1, y1], fill=(0, 0, 0))

        # text
        draw.text((x0 + padding, y0 + padding), label, fill=color, font=font)

        out_path = Path(RESULT_FOLDER) / f"{base_name}_result.jpeg"
        img.save(out_path, quality=95)

    # =========================
    # MAIN LOOP
    # =========================
    def run(self):

        files = sorted(Path(FOLDER).glob("*.h"))
        print(f"Found {len(files)} images\n")

        for f in files:

            try:
                base = f.stem

                img = self.load_image(f)
                self.send_image(img)

                result = self.receive_result()

                if result is None:
                    print(f"{f.name}: ERROR")
                    continue

                is_anomaly, score = result
                state = "ANOMALY" if is_anomaly else "NORMAL"

                print(f"{f.name}: {state} ({score:.6f})")

                # NEW STEP
                self.save_result_image(base, score, is_anomaly)

            except Exception as e:
                print(f"{f.name}: ERROR ({e})")


# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    MCU().run()