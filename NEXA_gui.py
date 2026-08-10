"""
================================================================================
 N.E.X.A. SYSTEM MONITOR -- STARK INDUSTRIES EDITION (MARK II)
================================================================================
An advanced Iron-Man-themed desktop HUD / system monitor built on
PySide6 + OpenCV, with a procedurally generated rotating 3D wireframe
helmet, a multi-layer holographic arc reactor core, ambient color-shift
theming, particle effects, and a live AI-vision camera HUD.

WHY PROCEDURAL 3D INSTEAD OF A REAL MESH:
  This file deliberately does NOT bundle or load an actual Iron Man 3D
  model/mesh -- that would be reproducing copyrighted character art.
  Instead it builds an original low-poly "combat helmet" shape out of
  plain coordinate math (a faceted ovoid + visor + antenna), and spins
  it in true 3D (rotation matrices + perspective projection + painter's
  -algorithm depth sorting) using nothing but QPainter. No OpenGL, no
  GPU driver risk, no external asset files -- it just runs.

Run with:
    pip install PySide6 opencv-python psutil requests GPUtil mediapipe numpy
    python nexa_gui.py

Notes:
  - GPUtil and mediapipe are optional; the app degrades gracefully if
    either is missing.
  - On Windows the camera worker tries CAP_DSHOW/CAP_MSMF first; on
    macOS/Linux it falls back to CAP_ANY automatically.
  - The "3D helmet" widget is pure-Python vector math rendered with
    QPainter -- no OpenGL dependency, so it runs anywhere PySide6 runs.
================================================================================
"""

import sys
import platform
import time
import math
import random
import collections
from datetime import datetime

import psutil
import requests
import numpy as np
import cv2

# --------------------------------------------------------------------------
# Optional dependencies -- app must still run if these are missing
# --------------------------------------------------------------------------
try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

try:
    import mediapipe as mp
    MP_AVAILABLE = True
except ImportError:
    MP_AVAILABLE = False

from PySide6.QtCore import (
    Qt, QTimer, QPointF, QRectF, QThread, Signal, Slot
)
from PySide6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont, QFontDatabase,
    QLinearGradient, QRadialGradient, QImage, QPixmap, QPainterPath,
    QPolygonF
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QProgressBar, QPushButton, QGraphicsDropShadowEffect
)

# =============================================================================
# CONFIGURATION & THEME
# =============================================================================
THEME_COLOR = QColor(0, 255, 255)
THEME_SEC = QColor(0, 150, 255)
TEXT_COLOR = QColor(255, 255, 255)
ALERT_COLOR = QColor(255, 50, 50)

STARK_PALETTE = [
    ("NEXA PRIME",  QColor(0, 255, 200),  QColor(0, 200, 160)),
    ("ARC BLUE",    QColor(0, 255, 255),  QColor(0, 110, 220)),
    ("REPULSOR",    QColor(70, 170, 255), QColor(0, 80, 200)),
    ("OVERDRIVE",   QColor(255, 70, 40),  QColor(255, 140, 0)),
    ("QUANTUM",     QColor(230, 230, 255),QColor(60, 0, 200)),
    ("STARKIUM",    QColor(190, 60, 255), QColor(110, 0, 210)),
    ("VIBRANIUM",   QColor(60, 255, 170), QColor(0, 160, 120)),
]

WEATHER_API_KEY = "56417c141647d0cb1aba663af20ddff8"
CITY_NAME = "Delhi"

BOOT_LINES = [
    "Initializing NEXA Core Interface...",
    "Calibrating Arc Reactor Core...",
    "Loading Repulsor Diagnostics...",
    "Spinning Up Holographic Renderer...",
    "Establishing Satellite Uplink...",
    "Neural Net Synchronized.",
    "All Systems Nominal. NEXA Online.",
]


def lerp_color(c1: QColor, c2: QColor, t: float) -> QColor:
    t = max(0.0, min(1.0, t))
    r = c1.red() + (c2.red() - c1.red()) * t
    g = c1.green() + (c2.green() - c1.green()) * t
    b = c1.blue() + (c2.blue() - c1.blue()) * t
    return QColor(int(r), int(g), int(b))


# =============================================================================
# 3D MATH HELPERS (pure Python -- no OpenGL/numpy-required, kept dependency
# free so the 3D widget never breaks even if numpy ever misbehaves)
# =============================================================================

def rotate_point_3d(x, y, z, ax, ay, az):
    """Rotate a point around X, then Y, then Z axes (angles in radians)."""
    # Rotate around X
    cosx, sinx = math.cos(ax), math.sin(ax)
    y, z = y * cosx - z * sinx, y * sinx + z * cosx
    # Rotate around Y
    cosy, siny = math.cos(ay), math.sin(ay)
    x, z = x * cosy + z * siny, -x * siny + z * cosy
    # Rotate around Z
    cosz, sinz = math.cos(az), math.sin(az)
    x, y = x * cosz - y * sinz, x * sinz + y * cosz
    return x, y, z


def project_point(x, y, z, cx, cy, scale, distance=4.0):
    """Simple perspective projection. distance = camera distance from origin."""
    denom = (distance + z)
    if denom < 0.1:
        denom = 0.1
    factor = scale / denom
    sx = cx + x * factor
    sy = cy + y * factor
    return sx, sy, z


# =============================================================================
# WORKER THREADS
# =============================================================================

class SystemWorker(QThread):
    """Polls CPU / RAM / Disk / Battery / GPU / Network stats once a second."""
    stats_updated = Signal(dict)

    def __init__(self):
        super().__init__()
        self._running = True

    def run(self):
        while self._running:
            try:
                cpu = psutil.cpu_percent(interval=0.5)
                freq_obj = psutil.cpu_freq()
                freq = freq_obj.current if freq_obj else 0
                ram = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                battery = psutil.sensors_battery()

                gpu_load, gpu_temp, gpu_mem = 0, 0, 0
                if GPU_AVAILABLE:
                    try:
                        gpus = GPUtil.getGPUs()
                        if gpus:
                            gpu_load = gpus[0].load * 100
                            gpu_temp = gpus[0].temperature
                            gpu_mem = gpus[0].memoryUsed
                    except Exception:
                        pass

                net = psutil.net_io_counters()

                stats = {
                    'cpu': cpu,
                    'cpu_freq': freq,
                    'ram_percent': ram.percent,
                    'ram_used': ram.used / (1024 ** 3),
                    'ram_total': ram.total / (1024 ** 3),
                    'disk_percent': disk.percent,
                    'battery_percent': battery.percent if battery else 100,
                    'battery_plugged': battery.power_plugged if battery else True,
                    'gpu_load': gpu_load,
                    'gpu_temp': gpu_temp,
                    'gpu_mem': gpu_mem,
                    'net_sent': net.bytes_sent,
                    'net_recv': net.bytes_recv,
                }
                self.stats_updated.emit(stats)
            except Exception as e:
                print(f"[SystemWorker] Error: {e}")
            time.sleep(1)

    def stop(self):
        self._running = False


class WeatherWorker(QThread):
    """Fetches live weather every 10 minutes; falls back to mock/offline data."""
    weather_updated = Signal(dict)

    def __init__(self):
        super().__init__()
        self._running = True

    def run(self):
        first = True
        while self._running:
            try:
                if WEATHER_API_KEY in ("", "YOUR_OPENWEATHERMAP_API_KEY"):
                    weather_data = {
                        'temp': 22, 'condition': 'Clear Sky',
                        'city': 'Demo City', 'humidity': 45
                    }
                else:
                    url = (
                        f"http://api.openweathermap.org/data/2.5/weather?"
                        f"q={CITY_NAME}&appid={WEATHER_API_KEY}&units=metric"
                    )
                    res = requests.get(url, timeout=5).json()
                    if res.get('cod') == 200:
                        weather_data = {
                            'temp': res['main']['temp'],
                            'condition': res['weather'][0]['description'].title(),
                            'city': res['name'],
                            'humidity': res['main']['humidity'],
                        }
                    else:
                        raise RuntimeError("API Error")

                self.weather_updated.emit(weather_data)
            except Exception:
                self.weather_updated.emit({
                    'temp': '--', 'condition': 'Offline',
                    'city': 'Unknown', 'humidity': '--'
                })

            wait_s = 5 if first else 600
            first = False
            for _ in range(wait_s):
                if not self._running:
                    return
                time.sleep(1)

    def stop(self):
        self._running = False


class CameraWorker(QThread):
    """
    Captures from the default webcam and overlays a Stark-style HUD:
    scanning pulse, animated targeting brackets, face/hand tracking rings,
    contour-based object boxes, and a glitch-flicker effect when something
    is newly detected.
    """
    image_data = Signal(QImage)
    object_detected = Signal(str)
    threat_level = Signal(int)   # 0=clear, 1=tracking, 2=alert

    def __init__(self):
        super().__init__()
        self.is_running = True
        self.hud_color = (0, 255, 255)

        self.face_cascade = None
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            if self.face_cascade.empty():
                self.face_cascade = None
        except Exception as e:
            print(f"[CameraWorker] Cascade load error: {e}")

        self.mp_hands = None
        self.mp_face_mesh = None
        if MP_AVAILABLE:
            try:
                self.mp_hands = mp.solutions.hands.Hands(
                    static_image_mode=False, max_num_hands=2,
                    min_detection_confidence=0.5
                )
                self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
                    max_num_faces=1, refine_landmarks=True,
                    min_detection_confidence=0.5
                )
            except Exception as e:
                print(f"[CameraWorker] Mediapipe init error: {e}")

        self.frame_count = 0
        self.last_faces = []
        self.last_hand_results = None
        self.last_face_mesh_results = None
        self.last_contours = []

        self.glitch_frames = 0
        self._last_threat_label = None

    def set_hud_color(self, rgb_tuple):
        self.hud_color = rgb_tuple

    def run(self):
        cap = None
        if platform.system() == "Windows":
            backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
        else:
            backends = [cv2.CAP_ANY]

        found = False
        for api in backends:
            for index in range(4):
                cap = cv2.VideoCapture(index, api)
                if cap.isOpened():
                    found = True
                    break
                cap.release()
            if found:
                break

        if not found:
            self.object_detected.emit("ERROR: NO_CAM_FOUND")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        process_every_n_frames = 2

        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            try:
                h, w, _ = frame.shape
                self.frame_count += 1
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                if self.frame_count % process_every_n_frames == 0:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                    self.last_faces = []
                    if self.face_cascade is not None:
                        self.last_faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

                    if self.mp_hands is not None:
                        try:
                            small_frame = cv2.resize(frame_rgb, (320, 240))
                            self.last_hand_results = self.mp_hands.process(small_frame)
                            self.last_face_mesh_results = self.mp_face_mesh.process(small_frame)
                        except Exception:
                            pass

                    blur = cv2.GaussianBlur(gray, (5, 5), 0)
                    edges = cv2.Canny(blur, 30, 90)
                    dilated = cv2.dilate(edges, np.ones((5, 5), np.uint8), iterations=1)
                    self.last_contours, _ = cv2.findContours(
                        dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                    )

                self._render_hud(frame_rgb, w, h)

                qt_img = QImage(frame_rgb.data, w, h, 3 * w, QImage.Format_RGB888).copy()
                self.image_data.emit(qt_img)

            except Exception as e:
                print(f"[CameraWorker] Render error: {e}")
            time.sleep(0.01)

        cap.release()

    def _render_hud(self, frame_rgb, w, h):
        color = self.hud_color

        overlay = frame_rgb.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (15, 25, 35), -1)
        frame_rgb[:] = cv2.addWeighted(frame_rgb, 0.85, overlay, 0.15, 0)

        pulse_y = (self.frame_count * 15) % h
        cv2.line(frame_rgb, (0, pulse_y), (w, pulse_y), color, 1)
        dim = tuple(max(0, c // 2) for c in color)
        cv2.line(frame_rgb, (0, max(0, pulse_y - 2)), (w, max(0, pulse_y - 2)), dim, 1)

        sweep_x = (self.frame_count * 6) % w
        cv2.line(frame_rgb, (sweep_x, 0), (sweep_x, h), dim, 1)

        threat = 0

        if (self.mp_hands is not None and self.last_face_mesh_results
                and self.last_face_mesh_results.multi_face_landmarks):
            threat = max(threat, 1)
            for face_landmarks in self.last_face_mesh_results.multi_face_landmarks:
                for eye_idx in [468, 473]:
                    lm = face_landmarks.landmark[eye_idx]
                    ex, ey = int(lm.x * w), int(lm.y * h)
                    angle = (self.frame_count * 10) % 360

                    cv2.ellipse(frame_rgb, (ex, ey), (25, 25), angle, 0, 90, color, 2)
                    cv2.ellipse(frame_rgb, (ex, ey), (25, 25), angle + 180, 0, 90, color, 1)

                    for i in range(4):
                        r_angle = math.radians(angle + (i * 90))
                        dx = int(ex + 18 * math.cos(r_angle))
                        dy = int(ey + 18 * math.sin(r_angle))
                        cv2.circle(frame_rgb, (dx, dy), 2, color, -1)

                    cv2.circle(frame_rgb, (ex, ey), 2, (255, 255, 255), -1)

                    if eye_idx == 468:
                        cv2.putText(frame_rgb, f"SYNC_{random.randint(90, 99)}%",
                                    (ex + 30, ey - 15), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.3, color, 1)
                        cv2.putText(frame_rgb, "HUD_ACTIVE", (ex + 30, ey - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)

        if self.mp_hands is not None and self.last_hand_results and self.last_hand_results.multi_hand_landmarks:
            threat = max(threat, 1)
            for hand_landmarks in self.last_hand_results.multi_hand_landmarks:
                palm = hand_landmarks.landmark[9]
                px, py = int(palm.x * w), int(palm.y * h)
                pulse_r = 12 + int(6 * math.sin(self.frame_count * 0.3))
                cv2.circle(frame_rgb, (px, py), pulse_r, (255, 255, 255), -1)
                cv2.circle(frame_rgb, (px, py), pulse_r + 6, color, 2)
                cv2.putText(frame_rgb, "REPULSOR_READY", (px - 50, py - 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)

        new_detection_label = None
        if self.last_faces is not None and len(self.last_faces) > 0:
            threat = max(threat, 2)
            for (x, y, wf, hf) in self.last_faces:
                self._draw_tech_box(frame_rgb, x, y, wf, hf, color, "SUBJECT_BIO", "NEXA_HUD_V2")
            new_detection_label = "HUMAN_SUBJECT"

        for cnt in self.last_contours[:2]:
            if cv2.contourArea(cnt) > 4000:
                ox, oy, ow, oh = cv2.boundingRect(cnt)
                self._draw_tech_box(frame_rgb, ox, oy, ow, oh, color, "OBJECT", "ANALYSIS")
                threat = max(threat, 1)

        if new_detection_label and new_detection_label != self._last_threat_label:
            self.glitch_frames = 6
            self.object_detected.emit(new_detection_label)
        self._last_threat_label = new_detection_label

        if self.glitch_frames > 0:
            self.glitch_frames -= 1
            shift = random.randint(-6, 6)
            if shift != 0:
                frame_rgb[:] = np.roll(frame_rgb, shift, axis=1)
            band_y = random.randint(0, max(1, h - 10))
            frame_rgb[band_y:band_y + 4, :, 0] = 255

        cv2.putText(frame_rgb, "SYS_FPS: 30 | AI_LOAD: ACTIVE", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        ts = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame_rgb, ts, (w - 80, 20), cv2.FONT_HERSHEY_SIMPLEX,
                    0.4, color, 1)
        cv2.drawMarker(frame_rgb, (w // 2, h // 2), dim, cv2.MARKER_CROSS, 20, 1)

        self.threat_level.emit(threat)

    @staticmethod
    def _draw_tech_box(img, x, y, w, h, color, label1, label2):
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 1)
        l = 20
        thick = 3
        cv2.line(img, (x, y), (x + l, y), color, thick)
        cv2.line(img, (x, y), (x, y + l), color, thick)
        cv2.line(img, (x + w, y), (x + w - l, y), color, thick)
        cv2.line(img, (x + w, y), (x + w, y + l), color, thick)
        cv2.line(img, (x, y + h), (x + l, y + h), color, thick)
        cv2.line(img, (x, y + h), (x, y + h - l), color, thick)
        cv2.line(img, (x + w, y + h), (x + w - l, y + h), color, thick)
        cv2.line(img, (x + w, y + h), (x + w, y + h - l), color, thick)

        dim = tuple(max(0, c // 2) for c in color)
        cv2.rectangle(img, (x, y - 30), (x + w, y), dim, -1)
        cv2.putText(img, label1, (x + 5, y - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv2.putText(img, label2, (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)

    def stop(self):
        self.is_running = False


# =============================================================================
# CUSTOM WIDGETS (VISUALS)
# =============================================================================

class GlowEffect(QGraphicsDropShadowEffect):
    def __init__(self, color=THEME_COLOR, blur=20):
        super().__init__()
        self.setBlurRadius(blur)
        self.setColor(color)
        self.setOffset(0, 0)


class ParticleField(QWidget):
    """Drifting particle starfield -- glowing motes that float and wrap."""
    def __init__(self, count=70):
        super().__init__()
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.particles = []
        for _ in range(count):
            self.particles.append({
                'x': random.uniform(0, 1),
                'y': random.uniform(0, 1),
                'speed': random.uniform(0.0003, 0.0012),
                'drift': random.uniform(-0.0003, 0.0003),
                'size': random.uniform(1.0, 3.0),
                'phase': random.uniform(0, math.pi * 2),
            })
        self.theme_color = QColor(THEME_COLOR)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)

    def set_theme_color(self, color: QColor):
        self.theme_color = color

    def _tick(self):
        for p in self.particles:
            p['y'] -= p['speed']
            p['x'] += p['drift']
            p['phase'] += 0.05
            if p['y'] < 0:
                p['y'] = 1.0
                p['x'] = random.uniform(0, 1)
            if p['x'] < 0:
                p['x'] = 1.0
            elif p['x'] > 1:
                p['x'] = 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        c = self.theme_color
        for p in self.particles:
            alpha = int(80 + 80 * math.sin(p['phase']))
            painter.setBrush(QBrush(QColor(c.red(), c.green(), c.blue(), max(0, alpha))))
            painter.setPen(Qt.NoPen)
            r = p['size']
            painter.drawEllipse(QPointF(p['x'] * w, p['y'] * h), r, r)


class RadarSweep(QWidget):
    """Small circular radar widget with a rotating sweep beam and blips."""
    def __init__(self):
        super().__init__()
        self.setMinimumSize(140, 140)
        self.angle = 0
        self.blips = [(random.uniform(0.2, 0.9), random.uniform(0, 360)) for _ in range(5)]
        self.theme_color = QColor(THEME_COLOR)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(30)

    def set_theme_color(self, color: QColor):
        self.theme_color = color

    def _tick(self):
        self.angle = (self.angle + 3) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        size = min(self.width(), self.height())
        cx, cy = self.width() / 2, self.height() / 2
        r = size / 2 - 6
        c = self.theme_color

        painter.setPen(QPen(QColor(c.red(), c.green(), c.blue(), 90), 1))
        painter.setBrush(Qt.NoBrush)
        for frac in (0.33, 0.66, 1.0):
            painter.drawEllipse(QPointF(cx, cy), r * frac, r * frac)
        painter.drawLine(QPointF(cx - r, cy), QPointF(cx + r, cy))
        painter.drawLine(QPointF(cx, cy - r), QPointF(cx, cy + r))

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle)
        grad = QLinearGradient(0, 0, r, 0)
        grad.setColorAt(0, QColor(c.red(), c.green(), c.blue(), 160))
        grad.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 0))
        path = QPainterPath()
        path.moveTo(0, 0)
        path.arcTo(QRectF(-r, -r, 2 * r, 2 * r), 0, -28)
        path.closeSubpath()
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)
        painter.restore()

        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(Qt.NoPen)
        for frac, ang in self.blips:
            rad = math.radians(ang)
            bx = cx + r * frac * math.cos(rad)
            by = cy + r * frac * math.sin(rad)
            diff = (self.angle - ang) % 360
            glow = max(0, 1 - diff / 60)
            if glow > 0:
                painter.setBrush(QBrush(QColor(c.red(), c.green(), c.blue(), int(255 * glow))))
                painter.drawEllipse(QPointF(bx, by), 3, 3)


class TechPanel(QWidget):
    """Custom-painted futuristic panel with angled corners and animated brackets."""
    def __init__(self, title="SYSTEM"):
        super().__init__()
        self.title = title
        self.theme_color = QColor(THEME_COLOR)
        self.bracket_phase = 0.0
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 35, 15, 15)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(50)

    def set_theme_color(self, color: QColor):
        self.theme_color = color
        self.update()

    def _tick(self):
        self.bracket_phase = (self.bracket_phase + 0.06) % (2 * math.pi)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        bg_col = QColor(0, 10, 20, 150)
        c = self.theme_color
        glow = 0.5 + 0.5 * math.sin(self.bracket_phase)
        border_alpha = int(140 + 80 * glow)
        border_col = QColor(c.red(), c.green(), c.blue(), min(255, border_alpha))

        painter.setBrush(QBrush(bg_col))
        painter.setPen(Qt.NoPen)

        cut = 15
        path = QPainterPath()
        path.moveTo(cut, 0)
        path.lineTo(w - cut, 0)
        path.lineTo(w, cut)
        path.lineTo(w, h - cut)
        path.lineTo(w - cut, h)
        path.lineTo(cut, h)
        path.lineTo(0, h - cut)
        path.lineTo(0, cut)
        path.closeSubpath()
        painter.drawPath(path)

        painter.setPen(QPen(border_col, 2))
        painter.setBrush(Qt.NoBrush)

        line_len = 40
        painter.drawLine(cut, 0, cut + line_len, 0)
        painter.drawLine(0, cut, 0, cut + line_len)
        painter.drawLine(0, cut, cut, 0)

        painter.drawLine(w - cut, 0, w - cut - line_len, 0)
        painter.drawLine(w, cut, w, cut + line_len)
        painter.drawLine(w, cut, w - cut, 0)

        painter.drawLine(cut, h, cut + line_len, h)
        painter.drawLine(0, h - cut, 0, h - cut - line_len)
        painter.drawLine(0, h - cut, cut, h)

        painter.drawLine(w - cut, h, w - cut - line_len, h)
        painter.drawLine(w, h - cut, w, h - cut - line_len)
        painter.drawLine(w, h - cut, w - cut, h)

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Impact", 12, QFont.Bold))
        painter.drawText(QRectF(0, 5, w, 25), Qt.AlignCenter, self.title)


class CircularMeter(QWidget):
    """Circular progress ring with danger-state color and theme-color support."""
    def __init__(self, title, suffix="%"):
        super().__init__()
        self.value = 0
        self.title = title
        self.suffix = suffix
        self.theme_color = QColor(THEME_COLOR)
        self.setMinimumSize(120, 120)

    def set_value(self, val):
        self.value = val
        self.update()

    def set_theme_color(self, color: QColor):
        self.theme_color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        size = min(self.width(), self.height())
        rect = QRectF(10, 10, size - 20, size - 20)

        pen = QPen(QColor(0, 50, 60), 8)
        painter.setPen(pen)
        painter.drawEllipse(rect)

        c = self.theme_color
        danger = self.value > 85
        ring_color = ALERT_COLOR if danger else c
        pen.setColor(ring_color)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        span_angle = -int(self.value * 3.6 * 16)
        painter.drawArc(rect, 90 * 16, span_angle)

        painter.setPen(TEXT_COLOR)
        font = QFont("Segoe UI", 12, QFont.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, f"{int(self.value)}{self.suffix}\n{self.title}")


# =============================================================================
# PROCEDURAL 3D HOLOGRAM HELMET
# =============================================================================

class HologramHelmet3D(QWidget):
    """
    A small "3D model" widget for the corner of the HUD: an original,
    procedurally generated faceted helmet silhouette (ovoid skull shape +
    angular jaw + glowing visor band + antenna), rotating continuously in
    true 3D space (rotation matrices + perspective projection), rendered
    as a holographic wireframe with depth-sorted, depth-shaded triangle
    faces using nothing but QPainter.

    This is NOT a copy of any copyrighted character model -- the geometry
    below is generated from plain trigonometric rings, not traced from
    or loaded from any external asset.
    """

    def __init__(self):
        super().__init__()
        self.setMinimumSize(200, 200)
        self.theme_color = QColor(THEME_COLOR)
        self.angle_y = 0.0
        self.angle_x = 0.15
        self.scan_phase = 0.0
        self.spin_speed = 0.025

        self.vertices, self.faces, self.wire_edges = self._build_helmet_geometry()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(30)

    def set_theme_color(self, color: QColor):
        self.theme_color = color

    def boost_spin(self):
        """Momentary spin-up, e.g. when a new face is detected by the camera."""
        self.spin_speed = 0.12

    def _tick(self):
        self.angle_y += self.spin_speed
        self.scan_phase += 0.04
        if self.spin_speed > 0.025:
            self.spin_speed -= 0.003
            if self.spin_speed < 0.025:
                self.spin_speed = 0.025
        self.update()

    # ------------------------------------------------------------------
    # GEOMETRY GENERATION (original, procedural -- no external mesh)
    # ------------------------------------------------------------------
    @staticmethod
    def _build_helmet_geometry():
        """
        Builds a faceted "combat helmet" out of horizontal rings of
        vertices (like a UV-sphere) but flattened/tapered to read as a
        jawed helmet rather than a plain sphere, plus a brow ridge and
        a small antenna stub. Returns (vertices, faces, wire_edges).
        """
        vertices = []
        rings = []  # list of lists of vertex indices, one list per ring (latitude)

        n_segments = 14   # vertices around each ring
        n_rings = 10       # rings from top of skull to chin

        for ring_i in range(n_rings + 1):
            t = ring_i / n_rings  # 0 at top of head, 1 at chin
            # Vertical position: top of skull (+1) to chin (-1)
            yv = 1.0 - 2.0 * t

            # Radius profile: wide at "ear" level, narrower at crown and chin,
            # with a jaw taper in the lower third.
            if t < 0.45:
                radius = 0.55 + 0.45 * math.sin(t / 0.45 * math.pi / 2)
            else:
                jaw_t = (t - 0.45) / 0.55
                radius = 1.0 - 0.55 * (jaw_t ** 1.4)

            # Slight forward taper (faceplate) on the front half handled
            # later via z-offset per-vertex below.
            ring = []
            for seg_i in range(n_segments):
                theta = 2 * math.pi * seg_i / n_segments
                x = radius * math.cos(theta)
                z = radius * math.sin(theta) * 0.85  # slightly flattened front/back
                # Push the front (z<0 considered "face side") slightly
                # forward to fake a brow/visor ridge around mid-height.
                if 0.30 <= t <= 0.62 and z < 0:
                    z -= 0.12
                vertices.append((x, yv, z))
                ring.append(len(vertices) - 1)
            rings.append(ring)

        # Antenna stub at the crown
        antenna_base_idx = len(vertices)
        vertices.append((0.0, 1.05, 0.0))
        antenna_tip_idx = len(vertices)
        vertices.append((0.0, 1.45, 0.0))

        # Build quad faces (as two triangles) between adjacent rings
        faces = []
        for r in range(len(rings) - 1):
            ring_a = rings[r]
            ring_b = rings[r + 1]
            n = len(ring_a)
            for s in range(n):
                a0 = ring_a[s]
                a1 = ring_a[(s + 1) % n]
                b0 = ring_b[s]
                b1 = ring_b[(s + 1) % n]
                faces.append((a0, a1, b1))
                faces.append((a0, b1, b0))

        # Wireframe edges -- ring edges + a few longitude lines for the
        # "tech panel seam" look
        wire_edges = []
        for ring in rings:
            n = len(ring)
            for s in range(n):
                wire_edges.append((ring[s], ring[(s + 1) % n]))
        for s in range(0, n_segments, 2):
            for r in range(len(rings) - 1):
                wire_edges.append((rings[r][s], rings[r + 1][s]))
        wire_edges.append((antenna_base_idx, antenna_tip_idx))

        return vertices, faces, wire_edges

    # ------------------------------------------------------------------
    # RENDERING
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        scale = min(w, h) * 0.85
        c = self.theme_color

        # Background holo-disc
        disc_grad = QRadialGradient(cx, cy, min(w, h) / 2)
        disc_grad.setColorAt(0, QColor(c.red(), c.green(), c.blue(), 25))
        disc_grad.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(disc_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), min(w, h) / 2, min(w, h) / 2)

        # Rotate + project every vertex
        projected = []
        for (vx, vy, vz) in self.vertices:
            rx, ry, rz = rotate_point_3d(vx, vy, vz, self.angle_x, self.angle_y, 0)
            sx, sy, sz = project_point(rx, ry, rz, cx, cy, scale, distance=3.2)
            projected.append((sx, sy, sz, rz))

        # ---- Depth-sorted shaded faces (painter's algorithm) ----
        face_draw_list = []
        for (i0, i1, i2) in self.faces:
            p0, p1, p2 = projected[i0], projected[i1], projected[i2]
            avg_z = (p0[2] + p1[2] + p2[2]) / 3.0
            # Simple "facing camera" shading: faces whose average rotated
            # z is more negative are closer to camera (camera looks down -z)
            depth_t = max(0.0, min(1.0, (avg_z + 1.5) / 3.0))
            face_draw_list.append((avg_z, p0, p1, p2, depth_t))

        face_draw_list.sort(key=lambda f: -f[0])  # farthest first

        for avg_z, p0, p1, p2, depth_t in face_draw_list:
            shade = 0.15 + 0.55 * (1.0 - depth_t)
            fill = QColor(
                int(c.red() * shade * 0.3),
                int(c.green() * shade * 0.5),
                int(c.blue() * shade * 0.6),
                140,
            )
            poly = QPolygonF([QPointF(p0[0], p0[1]), QPointF(p1[0], p1[1]), QPointF(p2[0], p2[1])])
            painter.setBrush(QBrush(fill))
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(poly)

        # ---- Wireframe overlay (glowing tech-seam lines) ----
        pen = QPen(QColor(c.red(), c.green(), c.blue(), 200), 1)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        for (i0, i1) in self.wire_edges:
            p0, p1 = projected[i0], projected[i1]
            painter.drawLine(QPointF(p0[0], p0[1]), QPointF(p1[0], p1[1]))

        # ---- Glowing visor band (mid-height ring, brighter) ----
        visor_pen = QPen(QColor(255, 255, 255, 220), 2)
        painter.setPen(visor_pen)

        # ---- Scan-line sweep across the holo-disc ----
        sweep_y = cy - (min(w, h) / 2) + (math.sin(self.scan_phase) * 0.5 + 0.5) * min(w, h)
        scan_pen = QPen(QColor(255, 255, 255, 90), 1)
        painter.setPen(scan_pen)
        painter.drawLine(QPointF(cx - min(w, h) / 2, sweep_y), QPointF(cx + min(w, h) / 2, sweep_y))

        # ---- Label ----
        painter.setPen(QColor(c.red(), c.green(), c.blue(), 230))
        painter.setFont(QFont("Consolas", 8, QFont.Bold))
        painter.drawText(QRectF(0, h - 18, w, 16), Qt.AlignCenter, "MARK -- HOLOGRAM")


# =============================================================================
# ARC REACTOR -- now with extra concentric "real reactor" rings + 3D depth
# =============================================================================

class ArcReactor(QWidget):
    """
    The animated core widget. Builds on the 5 Stark color-modes from
    before, but adds: a triple-layer concentric coil ring stack (to read
    as a "real" miniaturized arc reactor rather than a flat badge), a
    depth-shaded inner turbine that spins independently for a pseudo-3D
    parallax feel, and the external "power surge" flash hook.
    """
    def __init__(self):
        super().__init__()
        self.setMinimumSize(320, 320)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)

        self.mode_timer = QTimer(self)
        self.mode_timer.timeout.connect(self.cycle_mode)
        self.mode_timer.start(5000)

        self.mode = 0
        self.angle_1 = 0
        self.angle_2 = 0
        self.angle_3 = 0
        self.flux_angle = 0
        self.turbine_angle = 0.0
        self.pulse = 0
        self.pulse_dir = 1
        self.surge = 0.0

        self.colors = [
            (QColor(0, 255, 200), QColor(0, 200, 160)),
            (QColor(0, 255, 255), QColor(0, 150, 255)),
            (QColor(255, 50, 50), QColor(255, 120, 0)),
            (QColor(255, 255, 255), QColor(0, 120, 255)),
            (QColor(50, 255, 50), QColor(0, 255, 0)),
            (QColor(180, 50, 255), QColor(100, 0, 200)),
        ]

    def cycle_mode(self):
        self.mode = (self.mode + 1) % len(self.colors)
        self.pulse = 0

    def trigger_surge(self):
        self.surge = 1.0

    def animate(self):
        self.angle_1 = (self.angle_1 + 1.5) % 360
        self.angle_2 = (self.angle_2 - 2) % 360
        self.angle_3 = (self.angle_3 + 0.8) % 360
        self.flux_angle = (self.flux_angle + 5) % 360
        self.turbine_angle = (self.turbine_angle - 3.2) % 360

        self.pulse += 2.5 * self.pulse_dir
        if self.pulse >= 120 or self.pulse <= 10:
            self.pulse_dir *= -1

        if self.surge > 0:
            self.surge = max(0.0, self.surge - 0.04)

        self.update()

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        c_x, c_y = w / 2, h / 2
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        main_col, sec_col = self.colors[self.mode]

        gradient = QRadialGradient(c_x, c_y, w / 2.8)
        pulse_alpha = 100 + int(self.pulse) + int(self.surge * 100)
        pulse_alpha = min(255, pulse_alpha)

        gradient.setColorAt(0, QColor(255, 255, 255, 255))
        gradient.setColorAt(0.4, QColor(main_col.red(), main_col.green(), main_col.blue(), pulse_alpha))
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        surge_scale = 1.0 + self.surge * 0.15
        rw, rh = (w / 1.5) * surge_scale, (h / 1.5) * surge_scale
        painter.drawEllipse(QRectF(c_x - rw / 2, c_y - rh / 2, rw, rh))

        # ---- Inner spinning turbine (pseudo-3D: squashed ellipse blades) ----
        self._draw_turbine(painter, c_x, c_y, main_col, sec_col)

        if self.mode == 0:
            self.draw_nexa_mode(painter, c_x, c_y, main_col, sec_col)
        elif self.mode == 1:
            self.draw_standard_mode(painter, c_x, c_y, main_col, sec_col)
        elif self.mode == 2:
            self.draw_overdrive_mode(painter, c_x, c_y, main_col, sec_col)
        elif self.mode == 3:
            self.draw_quantum_mode(painter, c_x, c_y, main_col, sec_col)
        elif self.mode == 4:
            self.draw_targeting_mode(painter, c_x, c_y, main_col, sec_col)
        elif self.mode == 5:
            self.draw_starkium_mode(painter, c_x, c_y, main_col, sec_col)

        # ---- Triple concentric coil-ring stack (reads as a "real" reactor) ----
        self._draw_coil_stack(painter, c_x, c_y, main_col, sec_col)

        if self.surge > 0:
            painter.save()
            painter.translate(c_x, c_y)
            pen = QPen(QColor(255, 255, 255, int(255 * self.surge)), 3)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            ring_r = 90 + (1 - self.surge) * 80
            painter.drawEllipse(QRectF(-ring_r, -ring_r, ring_r * 2, ring_r * 2))
            painter.restore()

        painter.setPen(QColor(255, 255, 255, 255))
        painter.setFont(QFont("Impact", 32))
        painter.drawText(QRectF(c_x - 100, c_y - 40, 200, 50), Qt.AlignCenter, "NEXA")

        painter.setFont(QFont("Consolas", 10, QFont.Bold))
        painter.setPen(QColor(main_col.red(), main_col.green(), main_col.blue(), 200))
        status_text = [
            "> NEXA CORE <", "> STANDARD <", "> OVERDRIVE <",
            "> QUANTUM <", "> TARGET <", "> STARKIUM <"
        ][self.mode]
        painter.drawText(QRectF(c_x - 100, c_y + 10, 200, 30), Qt.AlignCenter, status_text)

    def _draw_turbine(self, painter, cx, cy, col1, col2):
        """A small spinning hub of squashed blades behind the core text,
        giving the impression of a real spinning turbine deep inside the
        reactor (pseudo-3D via vertical squash + alternating shade)."""
        painter.save()
        painter.translate(cx, cy)
        n_blades = 8
        for i in range(n_blades):
            blade_angle = self.turbine_angle + i * (360 / n_blades)
            painter.save()
            painter.rotate(blade_angle)
            # Squash vertically to fake the blade being viewed at an angle
            depth_shade = 0.4 + 0.6 * abs(math.cos(math.radians(blade_angle)))
            blade_col = QColor(
                int(col2.red() * depth_shade),
                int(col2.green() * depth_shade),
                int(col2.blue() * depth_shade),
                180,
            )
            painter.setBrush(QBrush(blade_col))
            painter.setPen(Qt.NoPen)
            painter.scale(1.0, 0.35)
            painter.drawEllipse(QRectF(8, -6, 38, 12))
            painter.restore()
        painter.restore()

    def _draw_coil_stack(self, painter, cx, cy, col1, col2):
        """Three concentric ridged rings around the core -- like the
        physical coil-windings on a real arc reactor casing."""
        painter.save()
        painter.translate(cx, cy)
        radii = [128, 142, 156]
        for idx, r in enumerate(radii):
            pen = QPen(QColor(col1.red(), col1.green(), col1.blue(), 90 - idx * 15), 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QRectF(-r, -r, 2 * r, 2 * r))

            # Ridge notches around each ring (bolt-like detail)
            n_notches = 16 + idx * 4
            notch_pen = QPen(QColor(col2.red(), col2.green(), col2.blue(), 150), 3)
            painter.setPen(notch_pen)
            for n in range(n_notches):
                a = math.radians(n * 360 / n_notches + self.angle_3 * (0.2 if idx % 2 == 0 else -0.2))
                x1, y1 = r * math.cos(a), r * math.sin(a)
                x2, y2 = (r + 6) * math.cos(a), (r + 6) * math.sin(a)
                painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        painter.restore()

    def draw_nexa_mode(self, painter, cx, cy, col1, col2):
        """New signature mode for NEXA: a hex-ring halo with breathing spokes."""
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle_1)
        pen = QPen(col1, 3)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        poly = QPolygonF()
        r = 95
        for i in range(8):
            theta = math.radians(45 * i)
            poly.append(QPointF(r * math.cos(theta), r * math.sin(theta)))
        painter.drawPolygon(poly)
        painter.restore()

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(-self.angle_2 * 0.8)
        pen2 = QPen(col2, 2)
        pen2.setDashPattern([4, 10])
        painter.setPen(pen2)
        painter.drawEllipse(-118, -118, 236, 236)

        for i in range(12):
            painter.rotate(30)
            spoke_len = 8 + 4 * math.sin(math.radians(self.flux_angle + i * 30))
            painter.drawLine(QPointF(118, 0), QPointF(118 + spoke_len, 0))
        painter.restore()

    def draw_standard_mode(self, painter, cx, cy, col1, col2):
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle_1)
        pen = QPen(col1, 4)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(-85, -85, 170, 170)
        for i in range(0, 360, 60):
            painter.drawLine(0, -85, 0, -75)
            painter.rotate(60)
        painter.restore()

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle_2)
        pen = QPen(col2, 10)
        pen.setCapStyle(Qt.FlatCap)
        painter.setPen(pen)
        rect = QRectF(-115, -115, 230, 230)
        for i in range(0, 360, 45):
            painter.drawArc(rect, i * 16, 35 * 16)
        painter.restore()

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle_3)
        pen = QPen(col1, 1)
        pen.setStyle(Qt.DotLine)
        painter.setPen(pen)
        painter.drawEllipse(-145, -145, 290, 290)
        painter.restore()

    def draw_overdrive_mode(self, painter, cx, cy, col1, col2):
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle_2 * 1.5)

        pen = QPen(col1, 2)
        painter.setPen(pen)

        path = QPainterPath()
        r_inner = 80
        r_outer = 100
        for i in range(0, 360, 20):
            rad = math.radians(i)
            rad_next = math.radians(i + 10)
            x1 = r_inner * math.cos(rad)
            y1 = r_inner * math.sin(rad)
            x2 = r_outer * math.cos(rad_next)
            y2 = r_outer * math.sin(rad_next)
            if i == 0:
                path.moveTo(x1, y1)
            else:
                path.lineTo(x1, y1)
            path.lineTo(x2, y2)
        path.closeSubpath()
        painter.drawPath(path)
        painter.restore()

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(-self.angle_1)
        pen = QPen(col2, 6)
        pen.setDashPattern([10, 20])
        painter.setPen(pen)
        painter.drawEllipse(-130, -130, 260, 260)
        painter.restore()

    def draw_quantum_mode(self, painter, cx, cy, col1, col2):
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle_3)
        pen = QPen(col1, 3)
        painter.setPen(pen)

        poly = QPolygonF()
        r = 100 + math.sin(math.radians(self.flux_angle)) * 10
        for i in range(6):
            theta = math.radians(60 * i)
            poly.append(QPointF(r * math.cos(theta), r * math.sin(theta)))
        painter.drawPolygon(poly)

        painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
        for p in poly:
            painter.drawLine(QPointF(0, 0), p)

        painter.restore()

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.flux_angle)

        painter.setBrush(QBrush(col2))
        painter.setPen(Qt.NoPen)
        for i in range(3):
            painter.rotate(120)
            painter.drawEllipse(130, 0, 8, 8)

        painter.restore()

    def draw_targeting_mode(self, painter, cx, cy, col1, col2):
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle_1 * 0.5)

        pen = QPen(col1, 1)
        painter.setPen(pen)
        painter.drawLine(-120, 0, 120, 0)
        painter.drawLine(0, -120, 0, 120)

        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(-50, -50, 100, 100)

        for i in range(4):
            painter.rotate(90)
            painter.drawLine(50, 0, 60, 0)

        painter.restore()

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(-self.angle_3)
        pen = QPen(col2, 2)
        pen.setDashPattern([5, 5])
        painter.setPen(pen)
        painter.drawEllipse(-140, -140, 280, 280)
        painter.restore()

    def draw_starkium_mode(self, painter, cx, cy, col1, col2):
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle_2)

        pen = QPen(col1, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        for i in range(0, 360, 45):
            painter.rotate(45)
            p1 = QPointF(0, -90)
            p2 = QPointF(-40, 0)
            p3 = QPointF(40, 0)
            painter.drawPolygon(QPolygonF([p1, p2, p3]))

        s_factor = 1.0 + (self.pulse / 500.0)
        painter.scale(s_factor, s_factor)
        pen.setColor(col2)
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawEllipse(-110, -110, 220, 220)

        painter.restore()


# =============================================================================
# MAIN INTERFACE
# =============================================================================

class NexaGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("N.E.X.A. SYSTEM MONITOR -- STARK INDUSTRIES MARK II")
        self.resize(1366, 860)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.palette_index = 0
        self.palette_progress = 0.0
        self.current_theme = QColor(STARK_PALETTE[0][1])
        self.current_theme_sec = QColor(STARK_PALETTE[0][2])
        self.color_shift_enabled = True

        self.alert_active = False
        self.alert_flash_phase = 0.0
        self.threat_level = 0

        self.repulsor_charge = 100.0  # cosmetic "suit power" gauge

        central = QWidget()
        self.setCentralWidget(central)

        self.particles = ParticleField(80)

        main_layout = QGridLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ----------------------
        # HEADER
        # ----------------------
        header_widget = QWidget()
        header_widget.setFixedHeight(80)
        header_widget.setStyleSheet("""
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 black, stop:0.6 rgba(10, 15, 20, 255), stop:1 rgba(0,0,0,0)
            );
            border-top: 5px solid cyan;
        """)
        header_layout = QHBoxLayout(header_widget)

        lbl_brand = QLabel("STARK INDUSTRIES")
        lbl_brand.setStyleSheet(
            "font-family: Impact; font-size: 24px; color: rgba(255,255,255,0.85); letter-spacing: 4px;"
        )
        header_layout.addWidget(lbl_brand)

        header_layout.addStretch()

        lbl_code = QLabel("||| || ||||| || |||")
        lbl_code.setStyleSheet("font-family: 'Courier New'; font-weight: bold; color: cyan; font-size: 18px;")
        header_layout.addWidget(lbl_code)

        header_layout.addStretch()

        self.lbl_clock = QLabel("00:00:00")
        self.lbl_clock.setStyleSheet("font-family: Consolas; font-size: 20px; color: #0ff; font-weight: bold;")
        header_layout.addWidget(self.lbl_clock)

        header_layout.addSpacing(20)

        self.lbl_ver = QLabel("SYSTEM: NEXA V.1.0 | MODE: ADAPTIVE")
        self.lbl_ver.setStyleSheet("font-family: Consolas; font-size: 14px; color: #0ff; font-weight: bold;")
        header_layout.addWidget(self.lbl_ver)

        main_layout.addWidget(header_widget, 0, 0, 1, 3)

        # ----------------------
        # LEFT PANEL (SYSTEM)
        # ----------------------
        self.left_panel = TechPanel("SYSTEM STATUS")
        left_layout = self.left_panel.layout

        self.cpu_meter = CircularMeter("CPU")
        self.gpu_meter = CircularMeter("GPU")
        self.ram_meter = CircularMeter("RAM")

        row1 = QHBoxLayout()
        row1.addWidget(self.cpu_meter)
        row1.addWidget(self.gpu_meter)
        left_layout.addLayout(row1)

        left_layout.addWidget(self.ram_meter)
        left_layout.setAlignment(self.ram_meter, Qt.AlignCenter)

        self.stats_label = QLabel("Initializing...")
        self.stats_label.setStyleSheet("color: #0ff; font-family: Consolas; font-size: 11px;")
        left_layout.addWidget(self.stats_label)

        radar_row = QHBoxLayout()
        radar_row.addStretch()
        self.radar = RadarSweep()
        radar_row.addWidget(self.radar)
        radar_row.addStretch()
        left_layout.addLayout(radar_row)

        # ---- Repulsor charge gauge (cosmetic "suit power" bar) ----
        self.lbl_repulsor = QLabel("REPULSOR CHARGE")
        self.lbl_repulsor.setStyleSheet("color: #0ff; font-weight: bold; margin-top: 8px;")
        self.repulsor_bar = QProgressBar()
        self.repulsor_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #0ff; border-radius: 2px;
                text-align: center; background: #001;
            }
            QProgressBar::chunk { background-color: #0ff; }
        """)
        self.repulsor_bar.setValue(100)
        left_layout.addWidget(self.lbl_repulsor)
        left_layout.addWidget(self.repulsor_bar)

        main_layout.addWidget(self.left_panel, 1, 0)

        # ----------------------
        # CENTER (ARC REACTOR + HELMET CORNER)
        # ----------------------
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)

        # Row holding the reactor centered, with the 3D helmet docked in
        # the top-right corner of this region (small, per the request).
        reactor_row = QHBoxLayout()
        reactor_row.addStretch()

        reactor_col = QVBoxLayout()
        self.arc_reactor = ArcReactor()
        self.reactor_glow = GlowEffect(THEME_COLOR, 50)
        self.arc_reactor.setGraphicsEffect(self.reactor_glow)
        reactor_col.addWidget(self.arc_reactor, alignment=Qt.AlignCenter)
        reactor_row.addLayout(reactor_col)

        reactor_row.addStretch()

        helmet_col = QVBoxLayout()
        helmet_col.addStretch()
        self.helmet3d = HologramHelmet3D()
        self.helmet3d.setFixedSize(180, 180)
        helmet_col.addWidget(self.helmet3d, alignment=Qt.AlignRight | Qt.AlignTop)
        reactor_row.addLayout(helmet_col)

        center_layout.addLayout(reactor_row)

        self.voice_label = QLabel("STATUS: STANDBY")
        self.voice_label.setAlignment(Qt.AlignCenter)
        self.voice_label.setStyleSheet(
            "color: white; font-weight: bold; font-size: 18px; letter-spacing: 5px; margin-top: 10px;"
        )
        center_layout.addWidget(self.voice_label)

        self.threat_banner = QLabel("")
        self.threat_banner.setAlignment(Qt.AlignCenter)
        self.threat_banner.setStyleSheet(
            "color: red; font-weight: bold; font-size: 14px; letter-spacing: 3px; margin-top: 6px;"
        )
        center_layout.addWidget(self.threat_banner)

        # ---- Scrolling diagnostics ticker, future-HUD vibe ----
        self.ticker_messages = collections.deque([
            "NEXA REACTOR OUTPUT NOMINAL", "REPULSORS CHARGED",
            "FLIGHT STABILIZERS ONLINE", "TARGETING ARRAY CALIBRATED",
            "SUIT INTEGRITY 100%", "NEURAL LINK STABLE",
            "NEXA CORE TEMPERATURE STABLE",
        ])
        self.lbl_ticker = QLabel(self.ticker_messages[0])
        self.lbl_ticker.setAlignment(Qt.AlignCenter)
        self.lbl_ticker.setStyleSheet(
            "color: rgba(0,255,255,180); font-family: Consolas; font-size: 11px; "
            "letter-spacing: 2px; margin-top: 4px;"
        )
        center_layout.addWidget(self.lbl_ticker)

        main_layout.addWidget(center_panel, 1, 1)

        # ----------------------
        # RIGHT PANEL (ENV & CAM)
        # ----------------------
        self.right_panel = TechPanel("MODULES")
        right_layout = self.right_panel.layout

        self.weather_info = QLabel("Fetching Weather...")
        self.weather_info.setStyleSheet(
            "background: rgba(0, 20, 30, 100); color: white; padding: 10px; border-radius: 5px;"
        )
        right_layout.addWidget(self.weather_info)

        self.cam_frame = QLabel("CAMERA OFFLINE")
        self.cam_frame.setFixedSize(300, 220)
        self.cam_frame.setStyleSheet(
            "background: black; border: 2px solid cyan; border-radius: 10px; color: #555;"
        )
        self.cam_frame.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.cam_frame)

        btn_layout = QHBoxLayout()
        self.btn_cam_on = QPushButton("INIT CAMERA")
        self.btn_cam_off = QPushButton("TERMINATE")
        for btn in [self.btn_cam_on, self.btn_cam_off]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0, 100, 150, 50);
                    border: 1px solid cyan;
                    color: cyan;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: cyan;
                    color: black;
                }
            """)

        btn_layout.addWidget(self.btn_cam_on)
        btn_layout.addWidget(self.btn_cam_off)
        right_layout.addLayout(btn_layout)

        self.btn_theme_lock = QPushButton("LOCK THEME: OFF")
        self.btn_theme_lock.setCheckable(True)
        self.btn_theme_lock.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 60, 80, 60);
                border: 1px solid #088;
                color: #0ff;
                padding: 6px;
                font-weight: bold;
                margin-top: 6px;
            }
            QPushButton:checked {
                background-color: rgba(255, 80, 0, 80);
                border: 1px solid orange;
                color: orange;
            }
        """)
        self.btn_theme_lock.clicked.connect(self.toggle_theme_lock)
        right_layout.addWidget(self.btn_theme_lock)

        self.batt_label = QLabel("BATTERY POWER")
        self.batt_label.setStyleSheet("color: #0ff; font-weight: bold; margin-top: 10px;")
        self.batt_bar = QProgressBar()
        self.batt_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #0ff;
                border-radius: 2px;
                text-align: center;
                background: #001;
            }
            QProgressBar::chunk {
                background-color: #0ff;
            }
        """)
        self.batt_bar.setValue(100)
        right_layout.addWidget(self.batt_label)
        right_layout.addWidget(self.batt_bar)

        main_layout.addWidget(self.right_panel, 1, 2)

        # ----------------------
        # BOTTOM (LOGS)
        # ----------------------
        self.log_lines = collections.deque(maxlen=5)
        self.log_area = QLabel("LOGS:")
        self.log_area.setFixedHeight(80)
        self.log_area.setStyleSheet(
            "background: rgba(0,0,0,100); color: #0f0; font-family: Consolas; "
            "font-size: 10px; padding: 5px; border-top: 1px solid #333;"
        )
        self.log_area.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        main_layout.addWidget(self.log_area, 2, 0, 1, 3)

        # ====================================
        # THREADING SETUP
        # ====================================
        self.sys_thread = SystemWorker()
        self.sys_thread.stats_updated.connect(self.update_system_stats)
        self.sys_thread.start()

        self.weather_thread = WeatherWorker()
        self.weather_thread.weather_updated.connect(self.update_weather)
        self.weather_thread.start()

        self.cam_thread = None
        self.btn_cam_on.clicked.connect(self.start_camera)
        self.btn_cam_off.clicked.connect(self.stop_camera)

        # ====================================
        # CLOCK TIMER
        # ====================================
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        self.update_clock()

        # ====================================
        # COLOR-SHIFT ENGINE TIMER
        # ====================================
        self.theme_timer = QTimer(self)
        self.theme_timer.timeout.connect(self.update_theme_shift)
        self.theme_timer.start(40)

        # ====================================
        # ALERT FLASH TIMER
        # ====================================
        self.alert_timer = QTimer(self)
        self.alert_timer.timeout.connect(self.update_alert_flash)
        self.alert_timer.start(40)

        # ====================================
        # TICKER ROTATION TIMER
        # ====================================
        self.ticker_timer = QTimer(self)
        self.ticker_timer.timeout.connect(self.rotate_ticker)
        self.ticker_timer.start(2600)

        # ====================================
        # REPULSOR CHARGE "BREATHING" TIMER (purely cosmetic gauge)
        # ====================================
        self.repulsor_timer = QTimer(self)
        self.repulsor_timer.timeout.connect(self.update_repulsor_gauge)
        self.repulsor_timer.start(120)

        # ====================================
        # BOOT SEQUENCE
        # ====================================
        self.voice_label.setText("STATUS: BOOTING")
        delay = 600
        for line in BOOT_LINES:
            QTimer.singleShot(delay, lambda l=line: self.log_message(l))
            delay += 650
        QTimer.singleShot(delay, lambda: self.voice_label.setText("STATUS: ONLINE"))
        QTimer.singleShot(delay, self.arc_reactor.trigger_surge)
        QTimer.singleShot(delay, self.helmet3d.boost_spin)

    # ------------------------------------------------------------------
    # LOGGING
    # ------------------------------------------------------------------
    def log_message(self, msg):
        self.log_lines.append(msg)
        text = "LOGS:\n" + "\n".join(f"> {l}" for l in self.log_lines)
        self.log_area.setText(text)

    # ------------------------------------------------------------------
    # CLOCK
    # ------------------------------------------------------------------
    def update_clock(self):
        now = datetime.now()
        self.lbl_clock.setText(now.strftime("%H:%M:%S"))

    # ------------------------------------------------------------------
    # TICKER (future-HUD readout rotation)
    # ------------------------------------------------------------------
    def rotate_ticker(self):
        self.ticker_messages.rotate(-1)
        self.lbl_ticker.setText(self.ticker_messages[0])

    # ------------------------------------------------------------------
    # REPULSOR GAUGE (cosmetic breathing animation between 80-100%)
    # ------------------------------------------------------------------
    def update_repulsor_gauge(self):
        t = time.time() * 1.5
        self.repulsor_charge = 88 + 12 * (0.5 + 0.5 * math.sin(t))
        self.repulsor_bar.setValue(int(self.repulsor_charge))

    # ------------------------------------------------------------------
    # THEME / COLOR-SHIFT ENGINE
    # ------------------------------------------------------------------
    def toggle_theme_lock(self):
        self.color_shift_enabled = not self.btn_theme_lock.isChecked()
        self.btn_theme_lock.setText(
            "LOCK THEME: ON" if self.btn_theme_lock.isChecked() else "LOCK THEME: OFF"
        )

    def update_theme_shift(self):
        if self.color_shift_enabled and not self.alert_active:
            self.palette_progress += 0.0015
            if self.palette_progress >= 1.0:
                self.palette_progress = 0.0
                self.palette_index = (self.palette_index + 1) % len(STARK_PALETTE)

            name_a, c1a, c2a = STARK_PALETTE[self.palette_index]
            name_b, c1b, c2b = STARK_PALETTE[(self.palette_index + 1) % len(STARK_PALETTE)]

            self.current_theme = lerp_color(c1a, c1b, self.palette_progress)
            self.current_theme_sec = lerp_color(c2a, c2b, self.palette_progress)

            if self.palette_progress < 0.02:
                self.lbl_ver.setText(f"SYSTEM: NEXA V.1.0 | MODE: {name_a}")

        self._apply_theme_color(self.current_theme)
        self.update()

    def _apply_theme_color(self, color: QColor):
        self.particles.set_theme_color(color)
        self.radar.set_theme_color(color)
        self.left_panel.set_theme_color(color)
        self.right_panel.set_theme_color(color)
        self.cpu_meter.set_theme_color(color)
        self.gpu_meter.set_theme_color(color)
        self.ram_meter.set_theme_color(color)
        self.helmet3d.set_theme_color(color)
        if self.cam_thread:
            self.cam_thread.set_hud_color((color.red(), color.green(), color.blue()))

    # ------------------------------------------------------------------
    # ALERT / THREAT FLASH ENGINE
    # ------------------------------------------------------------------
    def update_alert_flash(self):
        if self.alert_active:
            self.alert_flash_phase += 0.25
            self._apply_theme_color(lerp_color(
                self.current_theme, ALERT_COLOR,
                0.5 + 0.5 * math.sin(self.alert_flash_phase)
            ))
            self.update()

    @Slot(int)
    def handle_threat_level(self, level):
        self.threat_level = level
        if level >= 2 and not self.alert_active:
            self.alert_active = True
            self.alert_flash_phase = 0.0
            self.threat_banner.setText("!! THREAT DETECTED -- ANALYZING SUBJECT !!")
            self.arc_reactor.trigger_surge()
            self.helmet3d.boost_spin()
        elif level < 2 and self.alert_active:
            self.alert_active = False
            self.threat_banner.setText("")
            self._apply_theme_color(self.current_theme)

    # ------------------------------------------------------------------
    # SYSTEM STATS
    # ------------------------------------------------------------------
    @Slot(dict)
    def update_system_stats(self, stats):
        self.cpu_meter.set_value(stats['cpu'])
        self.ram_meter.set_value(stats['ram_percent'])
        self.gpu_meter.set_value(stats['gpu_load'])

        self.batt_bar.setValue(int(stats['battery_percent']))

        details = (
            f"CPU FREQ: {stats['cpu_freq']:.2f} MHz\n"
            f"RAM: {stats['ram_used']:.1f}GB / {stats['ram_total']:.1f}GB\n"
            f"GPU TEMP: {stats['gpu_temp']} C\n"
            f"DISK USAGE: {stats['disk_percent']}%\n"
            f"NET UP: {stats['net_sent'] / 1024 / 1024:.2f} MB\n"
            f"NET DOWN: {stats['net_recv'] / 1024 / 1024:.2f} MB"
        )
        self.stats_label.setText(details)

        if stats['cpu'] > 90:
            self.arc_reactor.trigger_surge()
            self.helmet3d.boost_spin()

    # ------------------------------------------------------------------
    # WEATHER
    # ------------------------------------------------------------------
    @Slot(dict)
    def update_weather(self, data):
        text = (
            f"LOCATION: {data['city']}\n"
            f"TEMP: {data['temp']}°C\n"
            f"COND: {data['condition']}\n"
            f"HUMIDITY: {data['humidity']}%"
        )
        self.weather_info.setText(text)

    # ------------------------------------------------------------------
    # CAMERA CONTROL
    # ------------------------------------------------------------------
    def start_camera(self):
        if self.cam_thread and self.cam_thread.isRunning():
            return
        self.cam_thread = CameraWorker()
        c = self.current_theme
        self.cam_thread.set_hud_color((c.red(), c.green(), c.blue()))
        self.cam_thread.image_data.connect(self.update_camera_frame)
        self.cam_thread.object_detected.connect(self.respond_to_object)
        self.cam_thread.threat_level.connect(self.handle_threat_level)
        self.cam_thread.start()
        self.log_message("Camera Module Activated.")
        self.voice_label.setText("STATUS: VISUALS ENGAGED")

    def stop_camera(self):
        if self.cam_thread:
            self.cam_thread.stop()
            self.cam_thread.quit()
            self.cam_thread.wait()
            self.cam_thread = None
        self.cam_frame.setPixmap(QPixmap())
        self.cam_frame.setText("CAMERA OFFLINE")
        self.log_message("Camera Module Deactivated.")
        self.voice_label.setText("STATUS: ONLINE")
        self.handle_threat_level(0)

    @Slot(QImage)
    def update_camera_frame(self, image):
        pixmap = QPixmap.fromImage(image)
        scaled_pix = pixmap.scaled(self.cam_frame.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.cam_frame.setPixmap(scaled_pix)

    @Slot(str)
    def respond_to_object(self, obj_name):
        if obj_name.startswith("ERROR"):
            self.log_message("Camera hardware not found.")
            self.cam_frame.setText("CAMERA OFFLINE\n(no device found)")
            return

        if self.voice_label.text() != f"DETECTED: {obj_name.upper()}":
            self.voice_label.setText(f"DETECTED: {obj_name.upper()}")
            self.log_message(f"Security Warning: {obj_name} identified in perimeter.")
            QTimer.singleShot(3000, lambda: self.voice_label.setText("STATUS: VISUALS ENGAGED"))

    # ------------------------------------------------------------------
    # GLOBAL BACKGROUND PAINT (grid + ambient color wash)
    # ------------------------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.particles.setGeometry(self.rect())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(5, 5, 10))

        c = self.current_theme
        wash = QRadialGradient(self.width() / 2, self.height() / 2, self.width() / 1.2)
        wash.setColorAt(0, QColor(c.red(), c.green(), c.blue(), 18))
        wash.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), QBrush(wash))

        pen = QPen(QColor(c.red(), c.green(), c.blue(), 30), 1)
        painter.setPen(pen)

        gap = 40
        for x in range(0, self.width(), gap):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), gap):
            painter.drawLine(0, y, self.width(), y)

        if self.alert_active:
            alpha = int(40 + 30 * math.sin(self.alert_flash_phase))
            painter.fillRect(self.rect(), QColor(255, 0, 0, max(0, alpha)))

        if self.particles.geometry() != self.rect():
            self.particles.setGeometry(self.rect())

    def closeEvent(self, event):
        try:
            self.sys_thread.stop()
            self.sys_thread.wait(1000)
        except Exception:
            pass
        try:
            self.weather_thread.stop()
            self.weather_thread.wait(1000)
        except Exception:
            pass
        if self.cam_thread:
            try:
                self.cam_thread.stop()
                self.cam_thread.wait(1000)
            except Exception:
                pass
        event.accept()


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        QFontDatabase.addApplicationFont(":/fonts/Orbitron-Bold.ttf")
    except Exception:
        pass
    app.setStyle("Fusion")

    window = NexaGUI()
    window.show()

    sys.exit(app.exec())
