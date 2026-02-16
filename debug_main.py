from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
# import cv2
# import numpy as np

ANDROID = False

class FingerScrollApp(App):
    """Main application class"""
    
    def __init__(self):
        super().__init__()
        self.capture = None
        self.tracking_active = False
        self.prev_frame = None
        self.scroll_cooldown = 0
        
        # Sensitivity settings
        self.sensitivity = 15  # Motion detection threshold
        self.scroll_speed = 300  # Scroll distance in pixels
        
    def build(self):
        """Build the UI"""
        
        # Main layout
        layout = FloatLayout()
        
        # Title
        title = Label(
            text='FINGER GESTURE SCROLL (DEBUG MODE)',
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
            text='• Move finger in TOP area = Scroll UP\n• Move finger in BOTTOM area = Scroll DOWN\n• Works in any app!',
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
        print("Toggle tracking pressed")
    
    def stop_app(self, instance):
        """Exit application"""
        self.stop()

if __name__ == '__main__':
    FingerScrollApp().run()
