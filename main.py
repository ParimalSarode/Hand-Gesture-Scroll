"""
Finger Gesture Scroll - Android App
Uses phone camera to detect index finger swipes and scroll any app (Instagram, YouTube, etc.)
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import cv2
import numpy as np
import mediapipe as mp
import time

# Android imports
try:
    from android.permissions import request_permissions, Permission
    from android.runnable import run_on_ui_thread
    from jnius import autoclass, cast
    ANDROID = True
    
    # Android classes for system control
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    View = autoclass('android.view.View')
    MotionEvent = autoclass('android.view.MotionEvent')
    SystemClock = autoclass('android.os.SystemClock')
    Instrumentation = autoclass('android.app.Instrumentation')
    
except ImportError:
    ANDROID = False
    print("Running in test mode (not Android)")
    
    def run_on_ui_thread(f):
        return f


class FingerScrollApp(App):
    """Main application class"""
    
    def __init__(self):
        super().__init__()
        self.capture = None
        self.tracking_active = False
        
        # MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Scroll logic
        self.prev_y = None
        self.scroll_triggered = False
        self.last_scroll_time = 0
        self.scroll_cooldown = 0.5  # Seconds between scrolls
        
        # Sensitivity settings
        self.swipe_threshold = 0.05  # Normalized distance (0.0 - 1.0)
        
    def build(self):
        """Build the UI"""
        
        # Request camera permission on Android
        if ANDROID:
            request_permissions([
                Permission.CAMERA,
                Permission.WRITE_EXTERNAL_STORAGE
            ])
        
        # Main layout
        layout = FloatLayout()
        
        # Title
        title = Label(
            text='GESTURE SCROLL - SWIPE MODE',
            size_hint=(1, 0.1),
            pos_hint={'x': 0, 'y': 0.9},
            font_size='24sp',
            bold=True,
            color=(0, 1, 0, 1)
        )
        layout.add_widget(title)
        
        # Camera URL Input
        self.url_input = TextInput(
            text='',
            hint_text='Enter DroidCam URL (e.g. http://192.168.1.5:4747/video)',
            size_hint=(0.8, 0.08),
            pos_hint={'x': 0.1, 'y': 0.82},
            multiline=False
        )
        layout.add_widget(self.url_input)

        # Status label
        self.status_label = Label(
            text='Enter URL above (or leave empty for webcam) & Press START',
            size_hint=(1, 0.1),
            pos_hint={'x': 0, 'y': 0.72},
            font_size='16sp',
            color=(1, 1, 1, 1)
        )
        layout.add_widget(self.status_label)
        
        # Camera preview
        self.camera_image = Image(
            size_hint=(1, 0.5),
            pos_hint={'x': 0, 'y': 0.2}
        )
        layout.add_widget(self.camera_image)
        
        # Instructions
        instructions = Label(
            text='• Move Index Finger UP to Scroll UP\n• Move Index Finger DOWN to Scroll DOWN\n',
            size_hint=(1, 0.15),
            pos_hint={'x': 0, 'y': 0.05},
            font_size='14sp',
            color=(0.7, 0.7, 0.7, 1)
        )
        layout.add_widget(instructions)
        
        # Control buttons
        button_box = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.1),
            pos_hint={'x': 0, 'y': 0},
            spacing=10,
            padding=10
        )
        
        self.start_button = Button(
            text='START',
            font_size='20sp',
            background_color=(0, 0.7, 0, 1),
            background_normal=''
        )
        self.start_button.bind(on_press=self.toggle_tracking)
        button_box.add_widget(self.start_button)
        
        exit_button = Button(
            text='EXIT',
            font_size='20sp',
            background_color=(0.7, 0, 0, 1),
            background_normal=''
        )
        exit_button.bind(on_press=self.stop_app)
        button_box.add_widget(exit_button)
        
        layout.add_widget(button_box)
        
        return layout
    
    def toggle_tracking(self, instance):
        """Start/stop finger tracking"""
        if not self.tracking_active:
            self.start_tracking()
        else:
            self.stop_tracking()
    
    def start_tracking(self):
        """Start camera and tracking"""
        if self.capture is None:
            url = self.url_input.text.strip()
            
            # Use URL if provided, otherwise try local webcam indices
            if url:
                print(f"Attempting to connect to: {url}")
                self.capture = cv2.VideoCapture(url)
            else:
                # Try to open camera (try indices 0, 1, 2)
                for i in range(3):
                    self.capture = cv2.VideoCapture(i)
                    if self.capture.isOpened():
                        break
            
            if self.capture and self.capture.isOpened():
                # Set camera properties for performance (only works for some backends)
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.capture.set(cv2.CAP_PROP_FPS, 30)
            else:
                 self.capture = None # Ensure it is None if failed

        if self.capture and self.capture.isOpened():
            self.tracking_active = True
            self.start_button.text = 'STOP'
            self.start_button.background_color = (0.7, 0, 0, 1)
            self.status_label.text = 'TRACKING ACTIVE - Show Index Finger!'
            
            # Start processing loop
            Clock.schedule_interval(self.process_frame, 1.0 / 30.0)
        else:
            self.status_label.text = 'ERROR: Cannot open camera! Check URL/Connection.'
    
    def stop_tracking(self):
        """Stop tracking"""
        self.tracking_active = False
        self.start_button.text = 'START'
        self.start_button.background_color = (0, 0.7, 0, 1)
        self.status_label.text = 'Tracking stopped'
        
        Clock.unschedule(self.process_frame)
        
        if self.capture:
            self.capture.release()
            self.capture = None
        
        self.prev_y = None
    
    def process_frame(self, dt):
        """Process camera frame and detect gestures using MediaPipe"""
        if not self.tracking_active or not self.capture:
            return
        
        ret, frame = self.capture.read()
        if not ret:
            self.status_label.text = 'Camera error!'
            return
        
        # Flip frame for mirror effect
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        # Check for hands
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                # Get Finger Tips
                index_tip = hand_landmarks.landmark[8]
                middle_tip = hand_landmarks.landmark[12]
                
                # Get Finger PIP (lower joint) for simple extension check
                index_pip = hand_landmarks.landmark[6]
                middle_pip = hand_landmarks.landmark[10]
                
                # Check if fingers are extended (Tip above PIP) - Note Y is inverted (0 is top)
                index_extended = index_tip.y < index_pip.y
                middle_extended = middle_tip.y < middle_pip.y
                
                current_y = index_tip.y
                
                # Draw circle on active finger(s)
                if index_extended:
                    cx, cy = int(index_tip.x * w), int(index_tip.y * h)
                    color = (0, 255, 0) if not middle_extended else (0, 255, 255) # Green for 1, Yellow for 2
                    cv2.circle(frame, (cx, cy), 15, color, cv2.FILLED)
                
                if middle_extended:
                    cx, cy = int(middle_tip.x * w), int(middle_tip.y * h)
                    cv2.circle(frame, (cx, cy), 15, (0, 255, 255), cv2.FILLED)

                # Calculate Movement
                if self.prev_y is not None:
                    dy = current_y - self.prev_y
                    current_time = time.time()
                    
                    if current_time - self.last_scroll_time > self.scroll_cooldown:
                        
                        # SCROLL UP INTERACTION: swipe UP with TWO fingers (Index + Middle)
                        if dy < -self.swipe_threshold:  # Moving UP
                            if index_extended and middle_extended:
                                self.status_label.text = 'SWIPE UP (2 Fingers) -> Next!'
                                self.scroll_down() # App logic: Swipe UP -> Scroll Content Down (Next)
                                self.last_scroll_time = current_time
                                self.prev_y = None
                            else:
                                self.status_label.text = 'Use 2 Fingers to Scroll Up'
                                
                        # SCROLL DOWN INTERACTION: swipe DOWN with ONE finger (Index only)
                        elif dy > self.swipe_threshold:  # Moving DOWN
                            if index_extended and not middle_extended:
                                self.status_label.text = 'SWIPE DOWN (1 Finger) -> Prev!'
                                self.scroll_up() # App logic: Swipe DOWN -> Scroll Content Up (Prev)
                                self.last_scroll_time = current_time
                                self.prev_y = None
                            elif index_extended and middle_extended:
                                self.status_label.text = 'Show only 1 Finger to Scroll Down'   
                    
                    else:
                        self.status_label.text = '...cooldown...'
                else:
                    move_text = "Tracking..."
                    if index_extended and middle_extended:
                        move_text = "Ready to Scroll Up (Move Up)"
                    elif index_extended:
                        move_text = "Ready to Scroll Down (Move Down)"
                    self.status_label.text = move_text

                # Update previous position
                self.prev_y = current_y

        else:
            self.status_label.text = 'No Hand Detected'
            self.prev_y = None
        
        # Convert frame to texture for display
        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(w, h), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.camera_image.texture = texture
    
    def scroll_up(self):
        """Perform scroll up action"""
        if ANDROID:
            self.perform_android_scroll(up=True)
        else:
            print("SCROLL UP ACTION TRIGGERED")
    
    def scroll_down(self):
        """Perform scroll down action"""
        if ANDROID:
            self.perform_android_scroll(up=False)
        else:
            print("SCROLL DOWN ACTION TRIGGERED")
    
    @run_on_ui_thread
    def perform_android_scroll(self, up=True):
        """Perform actual scroll on Android using touch simulation"""
        try:
            # Get screen dimensions
            context = PythonActivity.mActivity
            display = context.getWindowManager().getDefaultDisplay()
            point = autoclass('android.graphics.Point')()
            display.getSize(point)
            
            screen_width = point.x
            screen_height = point.y
            
            # Define swipe coordinates
            # A scroll UP action usually means dragging finger DOWN on screen (content moves down)
            # A scroll DOWN action usually means dragging finger UP on screen (content moves up)
            # WAIT. Let's align with user intent: "Finger UP = Scroll UP".
            # If I scroll the mouse wheel UP, the page goes UP (I see content above).
            # To achieve this on a touch screen, I swipe DOWN.
            
            x = screen_width / 2
            
            if up:
                # Scroll UP (Show content above) -> Swipe DOWN on screen
                start_y = screen_height * 0.2
                end_y = screen_height * 0.8
            else:
                # Scroll DOWN (Show content below) -> Swipe UP on screen
                start_y = screen_height * 0.8
                end_y = screen_height * 0.2
            
            # Create instrumentation to send touch events
            inst = Instrumentation()
            
            # Down event
            down_time = SystemClock.uptimeMillis()
            event_down = MotionEvent.obtain(
                down_time,
                down_time,
                MotionEvent.ACTION_DOWN,
                x,
                start_y,
                0
            )
            inst.sendPointerSync(event_down)
            
            # Move event (Simulate drag)
            move_time = down_time + 50
            steps = 5
            for i in range(steps):
                interp_y = start_y + (end_y - start_y) * ((i + 1) / steps)
                event_move = MotionEvent.obtain(
                    down_time,
                    move_time + (i * 10),
                    MotionEvent.ACTION_MOVE,
                    x,
                    interp_y,
                    0
                )
                inst.sendPointerSync(event_move)
            
            # Up event
            up_time = move_time + (steps * 10) + 10
            event_up = MotionEvent.obtain(
                down_time,
                up_time,
                MotionEvent.ACTION_UP,
                x,
                end_y,
                0
            )
            inst.sendPointerSync(event_up)
            
        except Exception as e:
            print(f"Scroll error: {e}")
    
    def stop_app(self, instance):
        """Exit application"""
        self.stop_tracking()
        self.stop()
    
    def on_stop(self):
        """Cleanup when app closes"""
        if self.capture:
            self.capture.release()


if __name__ == '__main__':
    FingerScrollApp().run()
