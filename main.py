from camera4kivy.preview import AnchorLayout
from kivymd.app import MDApp
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.button import (
    MDIconButton,
)
from kivy.graphics.texture import Texture
from IrisDetector import process_frame
from kivy.utils import platform
from kivy.clock import Clock
from kivymd.uix.boxlayout import MDBoxLayout
from PIL import Image
from kivymd.uix.anchorlayout import MDAnchorLayout
import io
import cv2
import numpy as np
from components.CameraFrame import CameraFrame
from components.HistoryScreen import HistoryScreen
from components.PictureFrame import PictureFrame
from kivymd.uix.screen import Screen
from colors import Colors
from components.ResultFrame import ResultFrame
from components.SelectPictureFrame import SelectPictureFrame
import os
from components.Snackbar import Snackbar
from dbManager import DBManager
import datetime
from utils.Android import ImageSelector


class IrisDetector(MDApp):

    def __init__(self):
        super().__init__()
        self.top_bar = None
        self.historyScreen = None
        self.screen = None
        self.layout = None
        self.history = None
        self.cameraPlaceholder = None
        self.cameraResultFrame = None
        self.cameraPictureFrame = None
        self.resultLabel = None
        self.takePicture = None
        self.pictureFrame = None
        self.selectPicture = None
        self.preview = None
        self.currentScreen = None
        self.selectPictureFrame = None
        self.bottomNavigation = None
        self.cameraScreen = None
        self.camera_screen_saved = False
        self.select_picture_saved = False
        self.snackbar = Snackbar()
        self.image_selector = ImageSelector(self.handle_selection)
        self.log = True

    def result_exists(self):
        exists = False
        if (
            self.resultLabel
            and self.resultLabel.get_result() != ""
            or self.cameraResultFrame
            and self.cameraResultFrame.get_result() != ""
        ):
            exists = True
        return exists

    def save_result(self, _):
        if self.result_exists():
            if self.select_picture_saved or self.camera_screen_saved:
                self.snackbar.show("Image already saved, choose another.")
                return
            date = datetime.datetime.now()
            timestamp = date.strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}.png"
            internal_path = DBManager.get_storage_path()
            full_image_path = os.path.join(internal_path, filename)
            db_path = DBManager.get_db_path()
            result = self.resultLabel.get_result()
            if self.currentScreen == "take_picture":
                result = self.cameraResultFrame
            DBManager.insert_image(db_path, filename, result)
            if self.currentScreen == "take_picture" and self.cameraPictureFrame:
                self.cameraPictureFrame.export_as_image().save(full_image_path)
                self.camera_screen_saved = True
                self.snackbar.show("Image saved.")
            elif self.currentScreen == "select_picture" and self.pictureFrame:
                self.pictureFrame.export_as_image().save(full_image_path)
                self.select_picture_saved = True
                self.snackbar.show("Image saved.")

    def display_result(self, texture, result):
        if self.currentScreen == "take_picture":
            if self.cameraPlaceholder:
                self.cameraPlaceholder.clear_widgets()
                self.cameraPlaceholder.add_widget(self.cameraPictureFrame)
                if self.cameraPictureFrame:
                    self.cameraPictureFrame.set_source(texture)
                if self.cameraResultFrame:
                    self.cameraResultFrame.set_text(
                        f"Iris to pupil ratio: {str(result)}"
                    )
            print("Take Picture")
        if self.currentScreen == "select_picture":
            if self.pictureFrame:
                self.pictureFrame.set_source(texture)
                self.resultLabel.set_text(f"Iris to pupil ratio: {str(result)}")
                self.selectPictureFrame.set_padding([0])
                self.selectPictureFrame.set_placeholder(self.pictureFrame)
            print("Select Picture")

    def handle_selection(self, input_source):
        if not input_source:
            return
        try:
            if isinstance(input_source, str):
                frame = cv2.imread(input_source)
            else:
                buffer = bytearray()
                chunk_size = 8192
                byte_array = bytearray(chunk_size)
                while True:
                    bytes_read = input_source.read(byte_array)
                    if bytes_read == -1:
                        break
                    buffer.extend(byte_array[:bytes_read])
                input_source.close()

                nparr = np.frombuffer(buffer, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            processed_frame, result = process_frame(frame)

            buf = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            buf = cv2.flip(buf, 0)

            def update_texture(dt):
                try:
                    texture = Texture.create(
                        size=(buf.shape[1], buf.shape[0]), colorfmt="rgb"
                    )
                    texture.blit_buffer(
                        buf.tobytes(), colorfmt="rgb", bufferfmt="ubyte"
                    )
                    self.display_result(texture, result)
                except Exception as tex_err:
                    if self.log:
                        print(f"Error in texture update: {tex_err}")
                    import traceback

                    traceback.print_exc()

            Clock.schedule_once(update_texture)

            if self.preview is not None:
                self.preview.disconnect_camera()
        except Exception as e:
            print(f"Error in handle_selection: {str(e)}")
            import traceback

            traceback.print_exc()
            self.resultLabel.set_text("Error processing image", Colors.SOFT_RED.value)

    def get_image(self, instance):
        self.image_selector.get_image(instance)

    def open_camera(self, _):
        self.currentScreen = "take_picture"
        if not self.top_bar.right_action_items:
            self.top_bar.right_action_items = [
                ["refresh", self.reset_selection],
                ["content-save", self.save_result],
            ]
        if platform == "android":
            from android.permissions import request_permissions, Permission

            request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE])
        if self.preview is None:
            self.preview = CameraFrame(aspect_ratio="4:3")
            if self.cameraPlaceholder is not None:
                self.cameraPlaceholder.add_widget(self.preview)
                self.preview.connect_camera(
                    sensor_resolution=(2048, 1536),
                    enable_video=False,
                    enable_analyze_pixels=True,
                    filepath_callback=self.get_path,
                )

    def get_path(self, path):
        if platform == "android":
            from os.path import join
            from android.storage import primary_external_storage_path

            if path.startswith("DCIM") or not path.startswith("/"):
                base = primary_external_storage_path()
                path = join(base, path)
        self.handle_selection(path)

    def take_picture(self, path):
        self.preview.capture_photo()
        if self.log:
            print(f"Picture taken, saved at {path}")

    def update_ui_with_texture(self, instance, texture):
        def update_texture(dt):
            try:
                if texture:
                    size = texture.size
                    buffer = texture.pixels
                    img_array = np.frombuffer(buffer, dtype=np.uint8).reshape(
                        size[1], size[0], 4
                    )

                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
                    img_array = cv2.flip(img_array, 0)
                    image_pil = Image.fromarray(img_array)
                    img_byte_arr = io.BytesIO()
                    image_pil.save(img_byte_arr, format="PNG")
                    img_byte_arr = img_byte_arr.getvalue()

                    loaded_image = Image.open(io.BytesIO(img_byte_arr))
                    img_data = np.array(loaded_image)
                    img_data, result = process_frame(img_data)
                    new_texture = Texture.create(
                        size=(img_data.shape[1], img_data.shape[0]), colorfmt="rgb"
                    )
                    new_texture.blit_buffer(
                        img_data.tobytes(), colorfmt="rgb", bufferfmt="ubyte"
                    )
                    self.display_result(new_texture, result)

                Clock.schedule_once(lambda dt: self.disconnect_camera, 0.5)

            except Exception as tex_err:
                print(f"Error in texture update: {tex_err}")
                import traceback

                traceback.print_exc()

        Clock.schedule_once(update_texture)

    def disconnect_camera(self, _):
        if self.preview is not None:
            self.preview.disconnect_camera()
            self.preview = None

    def create_select_picture_screen(self):
        self.selectPictureFrame = SelectPictureFrame(on_click=self.get_image)
        self.pictureFrame = PictureFrame(
            md_bg_color=Colors.LIGHT_GRAY.value,
            size_hint=(1, 1),
            padding="2dp",
            radius=[8],
        )

        self.resultLabel = ResultFrame()
        self.selectPictureFrame.add_widget(self.resultLabel)
        return self.selectPictureFrame

    def create_camera_screen(self):
        self.cameraScreen = MDBoxLayout(
            orientation="vertical",
            padding="10dp",
            spacing="10dp",
            md_bg_color=Colors.CRISP_WHITE.value,
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )

        self.cameraPictureFrame = PictureFrame(
            md_bg_color=Colors.LIGHT_GRAY.value,
            size_hint=(1, 1),
            padding="2dp",
            radius=[8],
        )
        self.cameraResultFrame = ResultFrame()
        self.cameraPlaceholder = MDAnchorLayout()
        centered_button_layout = AnchorLayout(size_hint=(1, 0.1))
        captureButton = MDIconButton(
            on_release=self.take_picture, icon="circle-slice-8", icon_size="40dp"
        )
        centered_button_layout.add_widget(captureButton)
        self.cameraScreen.add_widget(self.cameraPlaceholder)
        self.cameraScreen.add_widget(centered_button_layout)
        self.cameraScreen.add_widget(self.cameraResultFrame)
        return self.cameraScreen

    def create_history_screen(self):
        box_layout = MDBoxLayout(
            orientation="vertical", md_bg_color=Colors.LIGHT_GRAY.value
        )
        self.historyScreen = HistoryScreen()
        box_layout.add_widget(self.historyScreen)
        return box_layout

    def reset_selection(self, _):
        if self.currentScreen == "select_picture":
            if self.resultLabel.get_result() != "":
                self.selectPictureFrame.reset_screen()
                self.resultLabel.clear_result()
                self.select_picture_saved = False
        if self.currentScreen == "take_picture":
            if self.cameraResultFrame and self.cameraResultFrame.get_result() != "":
                if self.cameraPlaceholder:
                    self.cameraPlaceholder.clear_widgets()
                    self.cameraPlaceholder.add_widget(self.preview)
                    self.cameraResultFrame.clear_result()
                    self.camera_screen_saved = False

    def select_picture_screen(self, instance):
        self.currentScreen = "select_picture"
        self.disconnect_camera(instance)
        if not self.top_bar.right_action_items:
            self.top_bar.right_action_items = [
                ["refresh", self.reset_selection],
                ["content-save", self.save_result],
            ]

    def history_screen(self, instance):
        self.currentScreen = "history"
        self.disconnect_camera(instance)
        self.top_bar.right_action_items = []
        path = DBManager.get_db_path()
        data = DBManager.get_saved_data(path)
        self.historyScreen.set_data(data)

    def build(self):
        self.currentScreen = "select_picture"
        self.screen = Screen()
        self.preview = None
        self.layout = MDBoxLayout(orientation="vertical")
        self.pictureFrame = None
        self.cameraPictureFrame = None
        self.cameraPlaceholder = None
        self.top_bar = MDTopAppBar(
            title="Iris Detector",
            elevation=1,
            anchor_title="left",
            right_action_items=[
                ["refresh", self.reset_selection],
                ["content-save", self.save_result],
            ],
        )

        self.layout.add_widget(self.top_bar)

        self.bottomNavigation = MDBottomNavigation()

        self.selectPicture = MDBottomNavigationItem(
            name="select_picture", text="Select Picture", icon="image"
        )
        self.selectPicture.bind(on_tab_press=self.select_picture_screen)
        self.selectPicture.add_widget(self.create_select_picture_screen())
        self.bottomNavigation.add_widget(self.selectPicture)

        self.takePicture = MDBottomNavigationItem(
            name="take_picture", text="Take Picture", icon="camera"
        )
        self.takePicture.bind(on_tab_press=self.open_camera)

        self.takePicture.add_widget(self.create_camera_screen())
        self.bottomNavigation.add_widget(self.takePicture)

        self.history = MDBottomNavigationItem(
            name="history", text="History", icon="history"
        )
        self.history.bind(on_tab_press=self.history_screen)
        self.history.add_widget(self.create_history_screen())
        self.bottomNavigation.add_widget(self.history)

        self.layout.add_widget(self.bottomNavigation)

        self.screen.add_widget(self.layout)

        return self.screen


if __name__ == "__main__":
    IrisDetector().run()
