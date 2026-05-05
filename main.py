import cv2
import numpy as np
import threading
import os
import json
from datetime import datetime

import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.camera import Camera
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.graphics import Color, Line
from kivy.clock import Clock
from kivy.core.window import Window

import omr_scanner

# Silence popups
omr_scanner.BATCH = True

# Globals
APP_CSV_PATH = "grades.csv"
all_keys = omr_scanner.load_all_keys()

try:
    with open("regions.json") as f:
        custom_regions = json.load(f)
        for key in ["roll", "dob", "paper", "category", "sub_category", "gender", "answers_col1", "answers_col2", "answers_col3"]:
            if key in custom_regions:
                omr_scanner.REGIONS[key] = tuple(custom_regions[key])
except Exception:
    pass

# Clean UI styling constraints
BTN_KWARGS = {'size_hint_y': None, 'height': '50dp', 'background_color': (0.2, 0.6, 0.8, 1), 'color': (1,1,1,1)}

class CameraScreen(Screen):
    def __init__(self, **kwargs):
        super(CameraScreen, self).__init__(**kwargs)
        # Main layout
        layout = BoxLayout(orientation='vertical')
        
        # Camera area with overlay
        cam_layout = FloatLayout()
        self.camera = Camera(resolution=(1280, 720), play=True)
        cam_layout.add_widget(self.camera)
        
        # Draw camera overlay guides
        with cam_layout.canvas.after:
            Color(0, 1, 0, 1) # Green
            self.guide_box = Line(rectangle=(0,0,0,0), width=2)
        cam_layout.bind(pos=self.update_guides, size=self.update_guides)
        
        layout.add_widget(cam_layout)
        
        # Status Label
        self.status_label = Label(text='Align OMR sheet inside guides', size_hint_y=None, height='40dp')
        layout.add_widget(self.status_label)
        
        # Buttons
        btn_layout = BoxLayout(size_hint_y=None, height='50dp')
        
        capture_btn = Button(text='Capture', **BTN_KWARGS)
        capture_btn.bind(on_press=self.capture_and_scan)
        
        gallery_btn = Button(text='Gallery', **BTN_KWARGS)
        gallery_btn.bind(on_press=self.open_gallery)
        
        settings_btn = Button(text='Settings', **BTN_KWARGS)
        settings_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'settings'))
        
        btn_layout.add_widget(gallery_btn)
        btn_layout.add_widget(capture_btn)
        btn_layout.add_widget(settings_btn)
        
        layout.add_widget(btn_layout)
        self.add_widget(layout)

    def update_guides(self, instance, value):
        # Draw a box in the center 80% of the camera view
        w, h = instance.size
        x, y = instance.pos
        self.guide_box.rectangle = (x + w*0.1, y + h*0.1, w*0.8, h*0.8)

    def capture_and_scan(self, instance):
        if not self.camera.texture:
            self.status_label.text = "Camera not ready!"
            return
            
        self.status_label.text = "Scanning..."
        tex = self.camera.texture
        size = tex.size
        pixels = tex.pixels
        
        img_np = np.frombuffer(pixels, dtype=np.uint8).reshape(size[1], size[0], 4)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
        
        threading.Thread(target=self.process_frame, args=(img_bgr,)).start()

    def open_gallery(self, instance):
        content = BoxLayout(orientation='vertical')
        filechooser = FileChooserListView(path='.')
        content.add_widget(filechooser)
        
        btn_layout = BoxLayout(size_hint_y=None, height='50dp')
        select_btn = Button(text='Select', **BTN_KWARGS)
        cancel_btn = Button(text='Cancel', **BTN_KWARGS)
        btn_layout.add_widget(select_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(title="Choose Image", content=content, size_hint=(0.9, 0.9))
        
        def on_select(instance):
            if filechooser.selection:
                img_path = filechooser.selection[0]
                img = cv2.imread(img_path)
                if img is not None:
                    self.status_label.text = f"Scanning {os.path.basename(img_path)}..."
                    threading.Thread(target=self.process_frame, args=(img,)).start()
                popup.dismiss()
                
        select_btn.bind(on_press=on_select)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def process_frame(self, img_bgr):
        # Resize if huge
        h, w = img_bgr.shape[:2]
        if max(h, w) > 1500:
            s = 1500 / max(h, w)
            img_bgr = cv2.resize(img_bgr, (int(w * s), int(h * s)))
            
        results = omr_scanner.process_image_array(img_bgr, all_keys)
        Clock.schedule_once(lambda dt: self.go_to_review(results), 0)

    def go_to_review(self, results):
        self.status_label.text = 'Align OMR sheet inside guides'
        review_screen = self.manager.get_screen('review')
        review_screen.set_data(results)
        self.manager.current = 'review'

class ReviewScreen(Screen):
    def __init__(self, **kwargs):
        super(ReviewScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        layout.add_widget(Label(text="Review Scanned Data", font_size='20sp', size_hint_y=None, height='40dp'))
        
        self.grid = GridLayout(cols=2, spacing=5)
        
        # Define fields
        self.fields = {}
        fields_to_add = ["Roll", "DOB", "Paper", "Category", "SubCat", "Gender"]
        for f in fields_to_add:
            self.grid.add_widget(Label(text=f+":", halign="right", size_hint_x=0.3))
            inp = TextInput(multiline=False)
            self.fields[f.lower()] = inp
            self.grid.add_widget(inp)
            
        self.grid.add_widget(Label(text="Answers:", halign="right", size_hint_x=0.3))
        self.fields["answers"] = TextInput(multiline=True)
        self.grid.add_widget(self.fields["answers"])
        
        layout.add_widget(self.grid)
        
        self.score_label = Label(text="Score: N/A", size_hint_y=None, height='40dp')
        layout.add_widget(self.score_label)
        
        btn_layout = BoxLayout(size_hint_y=None, height='50dp', spacing=5)
        retake_btn = Button(text='Retake', **BTN_KWARGS)
        retake_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'camera'))
        
        save_btn = Button(text='Save to CSV', **BTN_KWARGS)
        save_btn.bind(on_press=self.save_data)
        
        btn_layout.add_widget(retake_btn)
        btn_layout.add_widget(save_btn)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
        self.error_state = False

    def set_data(self, data):
        if "error" in data:
            self.score_label.text = f"Error: {data['error']}"
            self.error_state = True
            for k in self.fields:
                self.fields[k].text = ""
        else:
            self.error_state = False
            self.fields['roll'].text = data.get('roll', '')
            self.fields['dob'].text = data.get('dob', '')
            self.fields['paper'].text = data.get('paper', '')
            self.fields['category'].text = data.get('category', '')
            self.fields['subcat'].text = data.get('subcat', '')
            self.fields['gender'].text = data.get('gender', '')
            self.fields['answers'].text = data.get('answers', '')
            self.score_label.text = f"Score: {data.get('score', '')}"

    def save_data(self, instance):
        if self.error_state:
            self.manager.current = 'camera'
            return
            
        record = {
            "image": "mobile_scan",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "roll_no": self.fields['roll'].text,
            "dob": self.fields['dob'].text,
            "gender": self.fields['gender'].text,
            "paper_set": self.fields['paper'].text,
            "category": self.fields['category'].text,
            "sub_category": self.fields['subcat'].text,
            "score": self.score_label.text.replace("Score: ", ""),
            "answers": self.fields['answers'].text
        }
        omr_scanner.save_csv(APP_CSV_PATH, record)
        print(f"Data saved to {APP_CSV_PATH}")
        self.manager.current = 'camera'

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super(SettingsScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        layout.add_widget(Label(text="Settings", font_size='24sp', size_hint_y=None, height='40dp'))
        
        grid = GridLayout(cols=2, spacing=5, size_hint_y=None, height='60dp')
        grid.add_widget(Label(text="CSV File:", size_hint_x=0.3))
        self.csv_input = TextInput(text=APP_CSV_PATH, multiline=False)
        grid.add_widget(self.csv_input)
        layout.add_widget(grid)
        
        layout.add_widget(Label(text="Answer Keys (A, B, C, D) [Type string of characters]:", size_hint_y=None, height='30dp'))
        
        self.key_inputs = {}
        for p in ["A", "B", "C", "D"]:
            row = BoxLayout(size_hint_y=None, height='40dp')
            row.add_widget(Label(text=f"Paper {p}:", size_hint_x=0.2))
            
            # Pre-load if exists
            val = ""
            try:
                if os.path.exists(f"{p}.txt"):
                    val = "".join(open(f"{p}.txt").read().split())
            except: pass
            
            inp = TextInput(text=val, multiline=False)
            self.key_inputs[p] = inp
            row.add_widget(inp)
            layout.add_widget(row)
            
        # Push to top
        layout.add_widget(Label(size_hint_y=1))
        
        btn_layout = BoxLayout(size_hint_y=None, height='50dp')
        save_btn = Button(text='Save & Back', **BTN_KWARGS)
        save_btn.bind(on_press=self.save_settings)
        btn_layout.add_widget(save_btn)
        
        layout.add_widget(btn_layout)
        self.add_widget(layout)
        
    def save_settings(self, instance):
        global APP_CSV_PATH, all_keys
        APP_CSV_PATH = self.csv_input.text
        
        # Save keys to disk and reload
        for p in ["A", "B", "C", "D"]:
            val = self.key_inputs[p].text.upper()
            if val:
                with open(f"{p}.txt", "w") as f:
                    f.write("\n".join(list(val)))
                    
        all_keys = omr_scanner.load_all_keys()
        self.manager.current = 'camera'

class OMRApp(App):
    def build(self):
        Window.clearcolor = (0.1, 0.1, 0.1, 1)
        sm = ScreenManager()
        sm.add_widget(CameraScreen(name='camera'))
        sm.add_widget(ReviewScreen(name='review'))
        sm.add_widget(SettingsScreen(name='settings'))
        return sm

if __name__ == '__main__':
    OMRApp().run()
