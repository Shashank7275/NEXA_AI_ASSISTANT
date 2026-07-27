import cv2
import mediapipe as mp
import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore, QtOpenGL
from PyQt5.QtWidgets import QApplication, QMainWindow, QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
import sys
import math
import time

class JarvisHologram(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.cap = cv2.VideoCapture(0)
        self.setWindowTitle("JARVIS - Stark Industries Holographic Interface")
        self.holo_panels = []
        self.particles = []
        self.grabbed_panel = None
        self.pinch_distance = 0
        self.zoom_level = 1.0
        
    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.1, 0.1, 0.2, 1.0)
        
    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w/h if h != 0 else 1, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        
    def generate_holo_panel(self, x, y, z, width=2.0, height=1.5):
        return {
            'pos': np.array([x, y, z]),
            'size': np.array([width, height, 0.1]),
            'rotation': np.array([0, 0, 0]),
            'content': 'STARK INDUSTRIES\nSYSTEM STATUS\nREACTOR: 98%\nSHIELDS: ONLINE',
            'grabbed': False
        }
    
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        gluLookAt(0, 0, 5, 0, 0, 0, 0, 1, 0)
        
        # Blue neon holographic glow
        glColor4f(0.0, 0.5, 1.0, 0.3)
        
        # Draw holographic panels
        for i, panel in enumerate(self.holo_panels):
            glPushMatrix()
            glTranslatef(panel['pos'][0], panel['pos'][1], panel['pos'][2])
            glRotatef(panel['rotation'][0], 1, 0, 0)
            glRotatef(panel['rotation'][1], 0, 1, 0)
            glRotatef(panel['rotation'][2], 0, 0, 1)
            
            # Panel frame with glow
            glLineWidth(3.0)
            glBegin(GL_LINE_LOOP)
            glVertex3f(-panel['size'][0]/2, -panel['size'][1]/2, 0)
            glVertex3f(panel['size'][0]/2, -panel['size'][1]/2, 0)
            glVertex3f(panel['size'][0]/2, panel['size'][1]/2, 0)
            glVertex3f(-panel['size'][0]/2, panel['size'][1]/2, 0)
            glEnd()
            
            # Glass panel surface
            glColor4f(0.0, 0.3, 0.8, 0.1)
            glBegin(GL_QUADS)
            glVertex3f(-panel['size'][0]/2, -panel['size'][1]/2, 0.01)
            glVertex3f(panel['size'][0]/2, -panel['size'][1]/2, 0.01)
            glVertex3f(panel['size'][0]/2, panel['size'][1]/2, 0.01)
            glVertex3f(-panel['size'][0]/2, panel['size'][1]/2, 0.01)
            glEnd()
            glPopMatrix()
        
        # Rotating circular HUD elements
        glPushMatrix()
        glTranslatef(0, 1.5, 0)
        glRotatef(time.time() * 30, 0, 0, 1)
        glColor4f(0.0, 0.7, 1.0, 0.6)
        glBegin(GL_LINE_LOOP)
        for i in range(32):
            angle = i * 2 * math.pi / 32
            r = 0.8 + 0.2 * math.sin(i * 0.5)
            glVertex2f(r * math.cos(angle), r * math.sin(angle))
        glEnd()
        glPopMatrix()
        
        # Energy particles reacting to hand movement
        for particle in self.particles:
            glPushMatrix()
            glTranslatef(particle['pos'][0], particle['pos'][1], particle['pos'][2])
            glColor4f(0.0, 1.0, 1.0, particle['alpha'])
            glutSolidSphere(0.02, 8, 8)
            glPopMatrix()
    
    def process_gestures(self, landmarks):
        if len(landmarks) == 0:
            return
            
        # Get thumb and index finger tips
        thumb_tip = landmarks[4]  # Thumb tip
        index_tip = landmarks[8]  # Index tip
        
        # Calculate distance between thumb and index (pinch gesture)
        dx = thumb_tip.x - index_tip.x
        dy = thumb_tip.y - index_tip.y
        self.pinch_distance = math.sqrt(dx*dx + dy*dy)
        
        # Pinch to zoom
        if self.pinch_distance < 0.03:
            self.zoom_level *= 1.05
        elif self.pinch_distance > 0.08:
            self.zoom_level *= 0.95
            
        # Hand position for grabbing
        hand_pos_3d = np.array([landmarks[9].x * 4 - 2, 
                               -(landmarks[9].y * 3 - 1.5), 
                               landmarks[9].z * 2])
        
        # Check panel collision and grab
        for panel in self.holo_panels:
            dist = np.linalg.norm(hand_pos_3d - panel['pos'])
            if dist < 0.8 and self.pinch_distance < 0.05:
                panel['grabbed'] = True
                self.grabbed_panel = panel
                break
        
        # Drag grabbed panel
        if self.grabbed_panel:
            self.grabbed_panel['pos'] += (hand_pos_3d - self.grabbed_panel['pos']) * 0.1
    
    def update_hologram(self):
        ret, frame = self.cap.read()
        if not ret:
            return
            
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.hands.HAND_CONNECTIONS)
                self.process_gestures(hand_landmarks.landmark)
                
                # Generate particles around hand
                hand_center = np.mean([hand_landmarks.landmark[0].x, hand_landmarks.landmark[9].x])
                self.particles.append({
                    'pos': np.array([hand_center*4-2, 0, 0]),
                    'alpha': 1.0,
                    'life': 60
                })
        
        # Update particles
        self.particles = [p for p in self.particles if p['life'] > 0]
        for p in self.particles:
            p['alpha'] *= 0.95
            p['life'] -= 1
            p['pos'][1] += 0.02
        
        cv2.imshow('JARVIS Camera Feed - Gesture Control', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.cap.release()
            cv2.destroyAllWindows()
    
    def timerEvent(self, event):
        self.update_hologram()
        self.update()

def main():
    app = QApplication(sys.argv)
    
    # Initialize holographic panels
    widget = JarvisHologram()
    widget.holo_panels = [
        widget.generate_holo_panel(0, 0, 0),
        widget.generate_holo_panel(2, 1, -1),
        widget.generate_holo_panel(-2, -1, 1)
    ]
    
    widget.resize(1200, 800)
    widget.show()
    widget.startTimer(33)  # ~30 FPS
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
