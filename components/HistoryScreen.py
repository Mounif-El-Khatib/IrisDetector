# GridLayout:
#         cols: 3
#         size_hint_y: None
#         height: '40dp'
#         spacing: '10dp'
#         padding: '10dp'
#
#         MDLabel:
#             text: 'Image'
#             size_hint_x: 1/3
#             width: '100dp'
#             font_style: 'H6'
#             bold: True
#             halign: 'center'
#             valign: 'middle'
#
#         MDLabel:
#             text: 'Iris to Pupil Ratio'
#             font_style: 'H6'
#             bold: True
#             size_hint_x: 1/3
#             halign: 'center'
#             valign: 'middle'
#
#         MDLabel:
#             text: 'Date'
#             font_style: 'H6'
#             bold: True
#             size_hint_x: 1/3
#             halign: 'center'
#             valign: 'middle'
#
#
from kivy.properties import StringProperty
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.fitimage.fitimage import FitImage
from kivymd.uix.card import MDCard
from kivy.app import App

Builder.load_string(
    """
<HistoryScreen>:
    orientation: 'vertical'
    spacing: '10dp'
    padding: '10dp'

    
    RecycleView:
        id: recycle_view
        viewclass: 'HistoryItem'
        RecycleGridLayout:
            cols: 1
            size_hint_y: None
            default_size: None, None
            default_size_hint: 1, None
            height: self.minimum_height
            spacing: '10dp'
"""
)


class HistoryScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.recycle_view.data = [
            {
                "image_path": "eye.jpg",
                "result": f"Result",
                "date": f"2023-10",
            }
        ]

    def get_data(self):
        return self.ids.recycle_view.data

    def set_data(self, L: list):
        data = [
            {
                "result": f"Iris to Pupil Ratio:\n{row[2]}",
                "image_path": f"{App.get_running_app().user_data_dir}/{row[1]}",
                "date": f"Saved on:\n{row[3]}",
            }
            for row in L
        ]
        self.ids.recycle_view.data = data


class HistoryItem(MDCard):
    image_path = StringProperty()
    result = StringProperty()
    date = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.spacing = "5dp"
        self.padding = "5dp"
        self.size_hint_y = None
        self.height = "200dp"
        self.radius = [0]

        self.image = FitImage(
            source=self.image_path,
            size_hint_x=1 / 3,
        )
        self.add_widget(self.image)

        self.result_label = MDLabel(
            text=self.result,
            font_style="H6",
            bold=True,
            size_hint_x=1 / 3,
            halign="center",
            valign="middle",
        )
        self.add_widget(self.result_label)

        self.date_label = MDLabel(
            text=self.date,
            font_style="Body2",
            size_hint_x=1 / 3,
            halign="center",
            valign="center",
        )
        self.add_widget(self.date_label)

        self.bind(image_path=self.update_image)
        self.bind(result=self.update_result)
        self.bind(date=self.update_date)

    def update_image(self, instance, value):
        self.image.source = value

    def update_result(self, instance, value):
        self.result_label.text = value

    def update_date(self, instance, value):
        self.date_label.text = value

