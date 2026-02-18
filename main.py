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
try:
    import pyautogui
except ImportError:
    pyautogui = None

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
        # Scroll logic variables
        self.last_scroll_time = 0
        self.scroll_cooldown = 1.0 # 1 second between scrolls (prevent rapid fire)
        self.hold_start_time = 0
        self.current_gesture = 0 # 0=None, 1=OneFinger, 2=TwoFingers
        self.gesture_duration_threshold = 0.5 # Hold for 0.5s to trigger

    def build(self):
        """Build the UI"""
        
        # UI Layout
        layout = FloatLayout()
        
        # Title
        title = Label(
            text='GESTURE SCROLL - HOLD MODE',
            size_hint=(1, 0.1),
            pos_hint={'x': 0, 'y': 0.9},
            font_size='24sp',
            bold=True
        )
        layout.add_widget(title)
        
        # Camera preview
        self.camera_image = Image(
            size_hint=(1, 0.6),
            pos_hint={'x': 0, 'y': 0.2}
        )
        layout.add_widget(self.camera_image)
        
        # Status/Instructions
        self.status_label = Label(
            text='Initializing Camera...',
            size_hint=(1, 0.1),
            pos_hint={'x': 0, 'y': 0.8},
            font_size='18sp',
            color=(0, 1, 0, 1),
            halign='center'
        )
        layout.add_widget(self.status_label)
        
        instructions = Label(
            text='• HOLD 1 Finger (0.5s) -> Scroll DOWN (Prev)\n• HOLD 2 Fingers (0.5s) -> Scroll UP (Next)',
            size_hint=(1, 0.15),
            pos_hint={'x': 0, 'y': 0.05},
            font_size='16sp',
            color=(0.9, 0.9, 0.9, 1)
        )
        layout.add_widget(instructions)
        
        # Auto-start camera after UI builds
        Clock.schedule_once(lambda dt: self.start_tracking(), 1.0)
        
        return layout
    
    def toggle_tracking(self, instance):
        """Start/stop finger tracking"""
        if not self.tracking_active:
            self.start_tracking()
        else:
            self.stop_tracking()
    
    def start_tracking(self):
        """Auto-start camera and tracking"""
        if self.capture is None:
            # Auto-scan for cameras (Test 0, 1, 2)
            print("Auto-scanning for cameras...")
            found_camera = False
            
            # Try indices. If user said 1 was working, we can try to test that.
            # We'll test availability by reading a frame.
            for i in [1, 0, 2]: # Prioritize 1 (External) as per user feedback
                temp_cap = cv2.VideoCapture(i)
                if temp_cap.isOpened():
                    # Optimization: Try to read a frame to ensure it's not a "ghost" camera
                    ret, _ = temp_cap.read()
                    if ret:
                        self.capture = temp_cap
                        print(f"Verified Camera at index {i}")
                        found_camera = True
                        break
                    else:
                        print(f"Camera at index {i} opened but failed to read frame.")
                        temp_cap.release()
                else:
                    temp_cap.release()
            
            if found_camera:
                # Set camera properties
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.capture.set(cv2.CAP_PROP_FPS, 30)
                
                self.tracking_active = True
                self.status_label.text = 'Camera Active!'
                Clock.schedule_interval(self.process_frame, 1.0/30.0)
            else:
                self.status_label.text = 'No working camera found!'
                self.status_label.color = (1, 0, 0, 1)
                self.capture = None
    
    def switch_camera(self, instance):
        """Cycle to the next available camera"""
        self.stop_tracking()
        # Logic to try next index could be complex to state management, 
        # simpler to just restart tracking which now prioritizes 1, then 0.
        # But if we want to force switch, we might need a counter.
        # For now, let's just re-trigger start which scans.
        self.start_tracking()

    def build(self):
        # UI Layout
        layout = FloatLayout()
        
        # Title
        title = Label(
            text='GESTURE SCROLL - HOLD MODE',
            size_hint=(1, 0.1),
            pos_hint={'x': 0, 'y': 0.9},
            font_size='24sp',
            bold=True
        )
        layout.add_widget(title)
        
        # Camera preview
        self.camera_image = Image(
            size_hint=(1, 0.6),
            pos_hint={'x': 0, 'y': 0.2}
        )
        layout.add_widget(self.camera_image)
        
        # Status/Instructions
        self.status_label = Label(
            text='Initializing Camera...',
            size_hint=(1, 0.1),
            pos_hint={'x': 0, 'y': 0.8},
            font_size='18sp',
            color=(0, 1, 0, 1),
            halign='center'
        )
        layout.add_widget(self.status_label)
        
        instructions = Label(
            text='• HOLD 1 Finger (0.5s) -> Scroll DOWN (Prev)\n• HOLD 2 Fingers (0.5s) -> Scroll UP (Next)',
            size_hint=(1, 0.15),
            pos_hint={'x': 0, 'y': 0.05},
            font_size='16sp',
            color=(0.9, 0.9, 0.9, 1)
        )
        layout.add_widget(instructions)
        
        # Auto-start camera after UI builds
        Clock.schedule_once(lambda dt: self.start_tracking(), 1.0)
        
        # RESTART Button (In case of camera error)
        restart_btn = Button(
            text='RESTART APP',
            size_hint=(0.3, 0.1),
            pos_hint={'x': 0.35, 'y': 0},
            background_color=(0, 0, 1, 1)
        )
        restart_btn.bind(on_press=self.restart_app)
        layout.add_widget(restart_btn)
        
        return layout

    def restart_app(self, instance):
        self.stop_tracking()
        self.start_tracking()
    
    def stop_tracking(self):
        """Stop tracking logic"""
        self.tracking_active = False
        self.start_button.text = 'START'
        self.start_button.background_color = (0, 0.7, 0, 1)
        Clock.unschedule(self.process_frame)
        if self.capture:
            self.capture.release()
            self.capture = None
        self.camera_image.texture = None
        self.status_label.text = 'Stopped'
    
    def process_frame(self, dt):
        """Process camera frame and detect gestures using MediaPipe (STATIC HOLD Logic)"""
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
        
        detected_gesture = 0 # Default: No gesture
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                # Get Key Landmarks
                wrist = hand_landmarks.landmark[0]
                
                # Index Finger
                index_tip = hand_landmarks.landmark[8]
                index_pip = hand_landmarks.landmark[6] # Middle joint
                
                # Middle Finger
                middle_tip = hand_landmarks.landmark[12]
                middle_pip = hand_landmarks.landmark[10]

                # Robust Extension Logic: Euclidean Distance
                # Index
                dist_index_tip = (index_tip.x - wrist.x)**2 + (index_tip.y - wrist.y)**2
                dist_index_pip = (index_pip.x - wrist.x)**2 + (index_pip.y - wrist.y)**2
                index_extended = dist_index_tip > dist_index_pip
                
                # Middle
                dist_middle_tip = (middle_tip.x - wrist.x)**2 + (middle_tip.y - wrist.y)**2
                dist_middle_pip = (middle_pip.x - wrist.x)**2 + (middle_pip.y - wrist.y)**2
                middle_extended = dist_middle_tip > dist_middle_pip
                
                # Count Fingers
                if index_extended and middle_extended:
                    detected_gesture = 2
                elif index_extended:
                    detected_gesture = 1
                else:
                    detected_gesture = 0

                # Visual Feedback
                color = (0, 0, 255) # Red (None)
                if detected_gesture == 1: color = (0, 255, 0) # Green
                if detected_gesture == 2: color = (0, 255, 255) # Yellow
                
                cv2.putText(frame, f"Fingers Detected: {detected_gesture}", (10, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                           
                # HOLD LOGIC
                current_time = time.time()
                
                # Check for gesture change
                if detected_gesture != self.current_gesture:
                    self.current_gesture = detected_gesture
                    self.hold_start_time = current_time # Reset timer
                    # print(f"Gesture Changed to: {detected_gesture}")
                
                else:
                    # Gesture is stable
                    hold_duration = current_time - self.hold_start_time
                    
                    # Show progress bar or text
                    if detected_gesture > 0:
                        progress = min(hold_duration / self.gesture_duration_threshold, 1.0)
                        bar_width = int(progress * 200)
                        cv2.rectangle(frame, (10, 60), (10 + bar_width, 70), color, -1)
                    
                    if hold_duration > self.gesture_duration_threshold:
                        # Threshold met! Trigger Action if cooldown passed
                        if current_time - self.last_scroll_time > self.scroll_cooldown:
                            
                            if detected_gesture == 1:
                                # 1 Finger -> Scroll Down (Prev)
                                self.status_label.text = "HOLD 1 -> Scroll Down (Prev)"
                                self.scroll_up() # App Logic Up = System Scroll Up (Prev)
                                self.last_scroll_time = current_time
                                
                            elif detected_gesture == 2:
                                # 2 Fingers -> Scroll Up (Next)
                                self.status_label.text = "HOLD 2 -> Scroll Up (Next)"
                                self.scroll_down() # App Logic Down = System Scroll Down (Next/PageDown)
                                self.last_scroll_time = current_time
                        else:
                            self.status_label.text = "...cooldown..."
                            
        else:
            self.status_label.text = 'No Hand Detected'
            self.current_gesture = 0
        
        # Convert frame to texture for display
        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.camera_image.texture = texture
    
    def scroll_up(self):
        """Perform scroll up action"""
        if ANDROID:
            self.perform_android_scroll(up=True)
        elif pyautogui:
            pyautogui.scroll(-300) # PC: Negative is down? Wait.
            # On Windows: 
            # Scroll UP (wheel forward) -> Content moves DOWN. 
            # App Logic: "Scroll Down" action (move finger down) means we want to see PREVIOUS content (scroll up).
            # Let's align with the app logic mapping:
            # self.scroll_down() was called when User swiped UP (2 fingers) -> "Next" -> Content moves UP -> Scroll Down
            
            # Wait, let's look at the mapping I set in process_frame:
            # Swipe UP (2 fingers) -> self.scroll_down() -> Next Item.
            # To go to Next Item on PC, we scroll the wheel DOWN (negative). 
            
            # Swipe DOWN (1 finger) -> self.scroll_up() -> Prev Item.
            # To go to Prev Item on PC, we scroll the wheel UP (positive).
            
            print("PC SCROLL: UP (Prev)")
            pyautogui.scroll(300)
        else:
            print("SCROLL UP ACTION TRIGGERED (pyautogui not found)")
    
    def scroll_down(self):
        """Perform scroll down action"""
        if ANDROID:
            self.perform_android_scroll(up=False)
        elif pyautogui:
            print("PC SCROLL: DOWN (Next)")
            pyautogui.scroll(-300)
        else:
            print("SCROLL DOWN ACTION TRIGGERED (pyautogui not found)")
    
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
