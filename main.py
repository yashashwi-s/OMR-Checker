import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.camera import Camera
from kivy.clock import Clock
import cv2
import numpy as np

class CameraScreen(Screen):
    def __init__(self, **kwargs):
        super(CameraScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        
        self.camera = Camera(resolution=(1280, 720), play=True)
        layout.add_widget(self.camera)
        
        btn_layout = BoxLayout(size_hint_y=0.2)
        capture_btn = Button(text='Capture & Scan', font_size='20sp')
        capture_btn.bind(on_press=self.capture_and_scan)
        btn_layout.add_widget(capture_btn)
        
        self.status_label = Label(text='Align OMR sheet and press Capture', size_hint_y=0.1)
        layout.add_widget(self.status_label)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)

    def capture_and_scan(self, instance):
        self.status_label.text = "Scanning..."
        # In a real app, we would extract the frame from self.camera.texture
        # Here we just mock the transition to review screen
        Clock.schedule_once(self.go_to_review, 1)

    def go_to_review(self, dt):
        self.manager.current = 'review'

class ReviewScreen(Screen):
    def __init__(self, **kwargs):
        super(ReviewScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        
        layout.add_widget(Label(text="Review Scanned Data", font_size='24sp', size_hint_y=0.2))
        
        self.data_label = Label(text="Roll: 123456789\nDOB: 01/01/2000\nScore: 45/50", size_hint_y=0.6)
        layout.add_widget(self.data_label)
        
        btn_layout = BoxLayout(size_hint_y=0.2)
        save_btn = Button(text='Save to CSV', font_size='20sp')
        save_btn.bind(on_press=self.save_data)
        cancel_btn = Button(text='Retake', font_size='20sp')
        cancel_btn.bind(on_press=self.go_to_camera)
        
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(save_btn)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)

    def save_data(self, instance):
        # Here we would append to grades.csv
        print("Data saved to CSV")
        self.manager.current = 'camera'

    def go_to_camera(self, instance):
        self.manager.current = 'camera'

class OMRApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(CameraScreen(name='camera'))
        sm.add_widget(ReviewScreen(name='review'))
        return sm

if __name__ == '__main__':
    OMRApp().run()
