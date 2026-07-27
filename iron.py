"""
Iron Man Repulsor Blast System - Advanced Hand Gesture Control
Shashank Singh's Stark Tech Implementation
"""

import cv2
import mediapipe as mp
import numpy as np
import pygame
import math
import time
from collections import deque
import threading

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

class RepulsorSystem:
    def __init__(self):
        # Pygame for audio and effects
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
        # Load sound effects (replace with your audio files)
        try:
            self.charge_sound = pygame.mixer.Sound("charge.wav")
            self.fire_sound = pygame.mixer.Sound("blast.wav")
            self.powerdown_sound = pygame.mixer.Sound("powerdown.wav")
        except:
            self.charge_sound = self.fire_sound = self.powerdown_sound = None
        
        # System states
        self.state = "IDLE"  # IDLE, CHARGING, READY, FIRING, COOLDOWN
        self.energy = 100
        self.max_energy = 100
        self.cooldown_time = 0
        self.stable_timer = 0
        self.charge_start_time = 0
        
        # Hand tracking
        self.palm_centers = deque(maxlen=10)
        self.hand_velocities = deque(maxlen=5)
        self.is_palm_open = False
        self.is_fist_closed = False
        
        # Visual effects
        self.particles = []
        self.blast_wave = 0
        self.screen_flash = 0
        self.target_lock_alpha = 0
        
        # HUD elements
        self.fps = 0
        self.last_time = time.time()
        self.energy_balls = []
        
    def detect_gestures(self, landmarks):
        """Advanced gesture detection using landmark analysis"""
        if landmarks is None or (hasattr(landmarks, "size") and landmarks.size == 0):
            return False, False
            
        # Palm center calculation (weighted average of key points)
        palm_points = [0, 1, 5, 9, 13, 17]  # Wrist, MCP joints
        palm_center = np.mean([landmarks[i][:2] for i in palm_points], axis=0)
        
        # Finger tip states (0=closed, 1=open)
        finger_tips = [4, 8, 12, 16, 20]
        finger_mcp = [2, 5, 9, 13, 17]
        
        fingers_open = []
        for tip, base in zip(finger_tips, finger_mcp):
            # Check if fingertip is above MCP (open) vs below (closed)
            if landmarks[tip][1] < landmarks[base][1]:
                fingers_open.append(True)
            else:
                fingers_open.append(False)
        
        # Palm open: 4+ fingers extended
        self.is_palm_open = sum(fingers_open) >= 4
        # Fist closed: 4+ fingers closed
        self.is_fist_closed = sum(fingers_open) <= 1
        
        self.palm_centers.append(palm_center)
        return self.is_palm_open, self.is_fist_closed
    
    def calculate_velocity(self):
        """Calculate forward velocity using palm center movement"""
        if len(self.palm_centers) < 2:
            return 0
            
        # Calculate velocity vector
        prev_center = self.palm_centers[-2]
        curr_center = self.palm_centers[-1]
        velocity = np.linalg.norm(np.array(curr_center) - np.array(prev_center))
        
        self.hand_velocities.append(velocity)
        if len(self.hand_velocities) > 1:
            avg_velocity = np.mean(self.hand_velocities)
            return avg_velocity
        return 0
    
    def update_state_machine(self, frame_shape, palm_center):
        self.frame_shape = frame_shape
        h, w = frame_shape[:2]
        
        # Stability detection for charging
        if self.is_palm_open:
            if self.state == "IDLE":
                self.stable_timer += 1
                if self.stable_timer >= 45:  # 1.5s at 30fps
                    self.state = "CHARGING"
                    self.charge_start_time = time.time()
                    if self.charge_sound:
                        self.charge_sound.play()
            elif self.state == "CHARGING":
                charge_duration = time.time() - self.charge_start_time
                if charge_duration >= 2.0:
                    self.state = "READY"
                    self.target_lock_alpha = 255
        else:
            self.stable_timer = 0
            if self.state in ["CHARGING", "READY"]:
                self.state = "IDLE"
                if self.powerdown_sound:
                    self.powerdown_sound.play()
        
        # Fist close → deactivate
        if self.is_fist_closed:
            self.state = "IDLE"
            self.stable_timer = 0
            self.target_lock_alpha *= 0.9
        
        # Firing logic
        if self.state == "READY":
            velocity = self.calculate_velocity()
            if velocity > 15:  # Forward push threshold
                self.fire_replusor(palm_center, w//2, h//2)
                self.emit_energy_ball(palm_center)
    
    def fire_replusor(self, palm_center, screen_center_x, screen_center_y):
        """Trigger repulsor blast with full effects"""
        self.state = "FIRING"
        self.energy = max(0, self.energy - 25)
        self.screen_flash = 120
        self.blast_wave = 50
        
        if self.fire_sound:
            self.fire_sound.play()
        
        # Create blast particles
        for _ in range(30):
            angle = np.random.uniform(0, 2*np.pi)
            speed = np.random.uniform(5, 15)
            self.particles.append({
                'pos': np.array(palm_center),
                'vel': np.array([np.cos(angle)*speed, np.sin(angle)*speed]),
                'life': 60,
                'max_life': 60
            })
    
    def emit_energy_ball(self, palm_center):
        if not hasattr(self, "frame_shape") or self.frame_shape is None:
            return
        h, w = self.frame_shape[:2]
        x = int(palm_center[0] * w)
        y = int(palm_center[1] * h)
        cx, cy = w // 2, h // 2
        dx = x - cx
        dy = y - cy
        norm = math.hypot(dx, dy)
        if norm == 0:
            norm = 1.0
        vx = (dx / norm) * 20.0
        vy = (dy / norm) * 20.0
        self.energy_balls.append({
            'pos': np.array([x, y], dtype=float),
            'vel': np.array([vx, vy], dtype=float),
            'radius': 12,
            'life': 60
        })
    
    def update_effects(self):
        """Update particle system and effects"""
        # Update particles (compatible with Python without walrus operator on subscripts)
        updated = []
        for p in self.particles:
            p['life'] -= 1
            if p['life'] > 0:
                p['pos'] += p['vel']
                p['vel'] *= 0.98  # Drag
                updated.append(p)
        self.particles = updated
        
        # Decay effects
        self.blast_wave *= 0.95
        self.screen_flash *= 0.92
        self.target_lock_alpha *= 0.96
        updated_balls = []
        for b in self.energy_balls:
            b['pos'] += b['vel']
            b['vel'] *= 0.99
            b['life'] -= 1
            if b['life'] > 0:
                updated_balls.append(b)
        self.energy_balls = updated_balls
    
    def draw_arc_reactor(self, frame, palm_center, radius=40):
        """Draw glowing arc reactor in palm"""
        h, w = frame.shape[:2]
        cx, cy = int(palm_center[0]*w), int(palm_center[1]*h)
        
        # Outer glow
        for i in range(5):
            alpha = int(100 * (1 - i/5) * (1 if self.state in ["CHARGING", "READY"] else 0.3))
            overlay = frame.copy()
            cv2.circle(overlay, (cx, cy), radius + i*8, (100, 200, 255), -1)
            cv2.addWeighted(overlay, alpha/255.0, frame, 1 - alpha/255.0, 0, frame)
        
        # Core reactor
        if self.state in ["CHARGING", "READY"]:
            pulse = 0.8 + 0.2 * math.sin(time.time() * 8)
            core_radius = int(radius * pulse)
            cv2.circle(frame, (cx, cy), core_radius, (0, 255, 255), 3)
            cv2.circle(frame, (cx, cy), int(core_radius*0.6), (100, 255, 255), -1)
    
    def draw_hud(self, frame):
        """Draw futuristic HUD overlay"""
        h, w = frame.shape[:2]
        
        # Dark cinematic overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (5, 5, 20), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        
        # Screen flash
        if self.screen_flash > 0:
            flash_overlay = frame.copy()
            cv2.rectangle(flash_overlay, (0, 0), (w, h), (200, 255, 255), -1)
            cv2.addWeighted(flash_overlay, self.screen_flash/255, frame, 1, 0, frame)
        
        # Target lock
        if self.target_lock_alpha > 10:
            center_x, center_y = w//2, h//2
            radius = int(50 * self.target_lock_alpha/255)
            cv2.circle(frame, (center_x, center_y), radius, (0, 255, 0), 3)
            cv2.line(frame, (center_x-30, center_y), (center_x+30, center_y), (0, 255, 0), 2)
            cv2.line(frame, (center_x, center_y-30), (center_x, center_y+30), (0, 255, 0), 2)
        
        # Energy meter
        meter_width = 300
        meter_height = 20
        energy_ratio = self.energy / self.max_energy
        x, y = 20, 40
        
        # Background
        cv2.rectangle(frame, (x, y), (x+meter_width, y+meter_height), (50, 50, 50), -1)
        # Energy bar
        fill_width = int(meter_width * energy_ratio)
        color = (0, 255, 0) if energy_ratio > 0.3 else (0, 255, 255)
        cv2.rectangle(frame, (x, y), (x+fill_width, y+meter_height), color, -1)
        cv2.rectangle(frame, (x, y), (x+meter_width, y+meter_height), (255, 255, 255), 2)
        
        # Status text
        font = cv2.FONT_HERSHEY_TRIPLEX
        if self.state == "READY":
            text = "REPULSOR READY"
            color = (0, 255, 255)
        elif self.energy < 20:
            text = "ENERGY LOW"
            color = (0, 100, 255)
        elif self.state == "FIRING":
            text = "FIRING!"
            color = (255, 100, 0)
        else:
            text = "STANDBY MODE"
            color = (150, 150, 150)
            
        cv2.putText(frame, text, (x, y-10), font, 1, color, 2)
        
        # HUD corners
        corners = [(20, h-40), (w-150, 20), (w-150, h-40)]
        corner_texts = [f"ENERGY: {self.energy}%", f"FPS: {self.fps}", "TARGET LOCKED"]
        for i, (cx, cy) in enumerate(corners):
            cv2.rectangle(frame, (cx-5, cy-25), (cx+150, cy+5), (20, 20, 60), 2)
            cv2.putText(frame, corner_texts[i], (cx, cy), font, 0.6, (150, 200, 255), 1)
    
    def draw_particles(self, frame):
        """Render particle effects"""
        h, w = frame.shape[:2]
        for p in self.particles:
            alpha = p['life'] / p['max_life']
            x, y = int(p['pos'][0]), int(p['pos'][1])
            if 0 <= x < w and 0 <= y < h:
                radius = int(3 * alpha)
                color_intensity = int(255 * alpha)
                color = (100, color_intensity, 255)
                cv2.circle(frame, (x, y), radius, color, -1)
    
    def draw_blast_wave(self, frame):
        """Draw expanding shockwave"""
        if self.blast_wave > 1:
            h, w = frame.shape[:2]
            center_x, center_y = w//2, h//2
            radius = int(self.blast_wave * 10)
            alpha = min(1.0, self.blast_wave / 50)
            overlay = frame.copy()
            cv2.circle(overlay, (center_x, center_y), radius, (255, 255, 150), 4)
            cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)
    
    def draw_energy_balls(self, frame):
        for b in self.energy_balls:
            x, y = int(b['pos'][0]), int(b['pos'][1])
            r = int(b['radius'])
            overlay = frame.copy()
            cv2.circle(overlay, (x, y), r + 6, (0, 255, 255), -1)
            cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)
            cv2.circle(frame, (x, y), r, (0, 255, 255), -1)

def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    system = RepulsorSystem()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame = cv2.flip(frame, 1)  # Mirror mode
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        palm_center = None
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=4),
                    mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2)
                )
                
                # Get normalized landmarks
                landmarks = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark])
                is_palm_open, is_fist_closed = system.detect_gestures(landmarks)
                
                # Calculate palm center
                palm_center = np.mean(landmarks[[0, 1, 5, 9, 13, 17]], axis=0)[:2]
        
        # Update system
        if palm_center is not None:
            system.update_state_machine(frame.shape, palm_center)
            system.draw_arc_reactor(frame, palm_center)
        else:
            system.is_palm_open = False
            system.is_fist_closed = False
            
        system.update_effects()
        system.draw_hud(frame)
        system.draw_particles(frame)
        system.draw_blast_wave(frame)
        system.draw_energy_balls(frame)
        
        # FPS counter
        curr_time = time.time()
        system.fps = int(1 / (curr_time - system.last_time))
        system.last_time = curr_time
        
        cv2.imshow('STARK REPULSOR SYSTEM v2.0', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    print("🔥 STARK REPULSOR SYSTEM INITIALIZING...")
    print("👋 Show OPEN PALM → CHARGE")
    print("⏱️  Hold stable 1.5s → READY")
    print("🚀 PUSH FORWARD → FIRE!")
    print("✊ CLOSED FIST → DEACTIVATE")
    print("Press 'q' to exit")
    main()
