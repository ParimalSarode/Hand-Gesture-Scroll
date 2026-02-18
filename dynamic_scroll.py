import cv2
import mediapipe as mp
import pyautogui
import time
import math

# Configuration
SCROLL_SENSITIVITY = 10    # Speed multiplier (Pixels per frame movement)
MOVEMENT_THRESHOLD = 0.01  # Increased threshold to ignore micro-jitters (1% of screen)
SCROLL_COOLDOWN = 0.05     # Seconds between scroll events to smoother output
DIRECTION_LOCK_THRESHOLD = 0.005 # Deadzone for opposite direction
SMOOTHING_FACTOR = 0.3     # Higher = More Responsive, Lower = Smoother (0.1 - 1.0)

class DynamicScrollApp:
    def __init__(self):
        # MediaPipe Init
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Camera Init
        # User reported webcam is at index 1
        self.cap = cv2.VideoCapture(1)
        if not self.cap.isOpened():
             print("Camera index 1 failed, trying index 0...")
             self.cap = cv2.VideoCapture(0)
             
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # State Variables
        self.prev_y = None # This will now store the SMOOTHED previous Y
        self.prev_time = time.time()
        self.is_tracking = False
        self.last_pause_time = 0.0
        self.is_active = False # Standby by default
        self.last_activation_time = 0.0
        self.smoothed_y = None # Current smoothed Y

        print("Dynamic Scroll App Started")
        print("--------------------------------")
        print("3 Fingers -> Toggle ON/OFF (Standby Mode)")
        print("1 Finger  -> Scroll DOWN (Move finger UP)")
        print("2 Fingers -> Scroll UP   (Move fingers DOWN)")
        print("FIST (0 Fing) -> PAUSE/PLAY (Media Key)")
        print("OPEN HAND (4+ Fing) -> PAUSE/PLAY (Media Key)")
        print("--------------------------------")
        print("Note: 'playpause' key toggles media. Works with YouTube/Spotify if they handle media keys.")
        print("--------------------------------")
        print("Press 'q' to quit.")

    def run(self):
        while self.cap.isOpened():
            success, image = self.cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            # Flip image for selfie view (User requested inverse camera movement, so checking if default is better)
            # image = cv2.flip(image, 1) # Disabled mirror
            H, W, _ = image.shape
            
            # Convert to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.hands.process(image_rgb)
            
            current_raw_y = None
            num_fingers = 0
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Always draw landmarks.
                    self.mp_draw.draw_landmarks(
                        image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    
                    # Get Key Landmarks
                    wrist = hand_landmarks.landmark[0]
                    index_tip = hand_landmarks.landmark[8]
                    current_raw_y = index_tip.y # Track index tip for scrolling
                    index_pip = hand_landmarks.landmark[6]
                    middle_tip = hand_landmarks.landmark[12]
                    middle_pip = hand_landmarks.landmark[10]
                    ring_tip = hand_landmarks.landmark[16]
                    ring_pip = hand_landmarks.landmark[14]
                    pinky_tip = hand_landmarks.landmark[20]
                    pinky_pip = hand_landmarks.landmark[18]
                    
                    # Apply Smoothing to Y
                    if self.smoothed_y is None:
                        self.smoothed_y = current_raw_y
                    else:
                        # EMA Formula: New = Alpha * RaW + (1-Alpha) * Old
                        self.smoothed_y = (SMOOTHING_FACTOR * current_raw_y) + ((1 - SMOOTHING_FACTOR) * self.smoothed_y)

                    # Always count fingers.
                    # Detect Fingers Extended (Distance from wrist comparison)
                    # Index
                    dist_index_tip = math.hypot(index_tip.x - wrist.x, index_tip.y - wrist.y)
                    dist_index_pip = math.hypot(index_pip.x - wrist.x, index_pip.y - wrist.y)
                    index_extended = dist_index_tip > dist_index_pip
                    
                    # Middle
                    dist_middle_tip = math.hypot(middle_tip.x - wrist.x, middle_tip.y - wrist.y)
                    dist_middle_pip = math.hypot(middle_pip.x - wrist.x, middle_pip.y - wrist.y)
                    middle_extended = dist_middle_tip > dist_middle_pip

                    # Ring
                    dist_ring_tip = math.hypot(ring_tip.x - wrist.x, ring_tip.y - wrist.y)
                    dist_ring_pip = math.hypot(ring_pip.x - wrist.x, ring_pip.y - wrist.y)
                    ring_extended = dist_ring_tip > dist_ring_pip

                    # Pinky
                    dist_pinky_tip = math.hypot(pinky_tip.x - wrist.x, pinky_tip.y - wrist.y)
                    dist_pinky_pip = math.hypot(pinky_pip.x - wrist.x, pinky_pip.y - wrist.y)
                    pinky_extended = dist_pinky_tip > dist_pinky_pip
                    
                    if index_extended: num_fingers += 1
                    if middle_extended: num_fingers += 1
                    if ring_extended: num_fingers += 1
                    if pinky_extended: num_fingers += 1
                    
                # Display Info
                cv2.putText(image, f"Fingers: {num_fingers}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Check for Activation (3 Fingers).
                # Toggle between Active and Standby
                if num_fingers == 3:
                    current_time = time.time()
                    if current_time - self.last_activation_time > 2.0: # 2s Cooldown
                        self.is_active = not self.is_active
                        self.last_activation_time = current_time
                        state_text = "ACTIVATED" if self.is_active else "STANDBY MODE"
                        print(f"State changed to: {state_text}")
                
                # Apply Visuals based on state.
                if self.is_active:
                    cv2.putText(image, "ACTIVE (3 Fing to Standby)", (10, 450), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # --- ACTIVE MODE LOGIC ---
                    
                    # PAUSE/PLAY LOGIC (Fist aka 0 FINGERS)
                    if num_fingers == 0:
                        current_time = time.time()
                        if current_time - self.last_pause_time > 2.0: # 2 Second Cooldown
                            print("PAUSE/PLAY TRIGGERED (Fist - Media Key)")
                            pyautogui.press('playpause')
                            self.last_pause_time = current_time
                            cv2.putText(image, "MEDIA TOGGLE", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                        else:
                            cv2.putText(image, "Cooldown...", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 1)

                    # RESUME LOGIC (Open Hand aka 4+ FINGERS)
                    elif num_fingers >= 4:
                        current_time = time.time()
                        if current_time - self.last_pause_time > 2.0: # 2 Second Cooldown
                            print("RESUME TRIGGERED (Open Hand - Media Key)")
                            pyautogui.press('playpause')
                            self.last_pause_time = current_time
                            cv2.putText(image, "MEDIA TOGGLE", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        else:
                            cv2.putText(image, "Cooldown...", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 1)

                    # Dynamic Scroll Logic
                    # We use self.smoothed_y for decision making to be stable
                    if self.prev_y is not None and self.smoothed_y is not None:
                        dy = self.smoothed_y - self.prev_y # +ve means moving DOWN, -ve means moving UP
                        
                        # Debugging Thresholds
                        # cv2.putText(image, f"DY: {dy:.4f}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                        # INVERTED LOGIC (Natural Scrolling)
                        # 1 Finger -> Scroll DOWN (User: "1 finger for scrolling down")
                        # Move Finger UP (dy < 0) -> Content moves UP -> View moves DOWN
                        if num_fingers == 1:
                            if dy < -MOVEMENT_THRESHOLD: # Moving UP significant amount
                                scroll_amount = -int(abs(dy) * 100 * SCROLL_SENSITIVITY) # Negative for scroll down
                                pyautogui.scroll(scroll_amount)
                                cv2.putText(image, "SCROLL DOWN", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                                # Only update prev_y if we actually scrolled, OR if we moved significantly
                                # To prevent "drifting", we update prev_y to current smoothed_y
                                # But if we only update when we scroll, we might get 'stuck'.
                                # Standard approach: always update prev_y to current smoothed_y at end of frame
                            
                        # 2 Fingers -> Scroll UP (User: "2 fingers for scrolling up")
                        # Move Fingers DOWN (dy > 0) -> Content moves DOWN -> View moves UP
                        elif num_fingers == 2:
                            if dy > MOVEMENT_THRESHOLD: # Moving DOWN significant amount
                                scroll_amount = int(abs(dy) * 100 * SCROLL_SENSITIVITY) # Positive for scroll up
                                pyautogui.scroll(scroll_amount)
                                cv2.putText(image, "SCROLL UP", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

                else:
                    cv2.putText(image, "STANDBY (Show 3 Fing to Activate)", (10, 450), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    # In Standby, we skip the action logic but still track prev_y reset below

                if self.smoothed_y is not None:
                    self.prev_y = self.smoothed_y
                else:
                    self.prev_y = None # Reset if hand lost
                    self.smoothed_y = None # Reset smoothing

            else:
                self.prev_y = None # Reset if no hand
                self.smoothed_y = None
            
            # Show Preview
            cv2.imshow('Dynamic Gesture Scroll', image)
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
                
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = DynamicScrollApp()
    app.run()
