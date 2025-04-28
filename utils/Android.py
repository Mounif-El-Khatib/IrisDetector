# image_utility.py
from kivy.utils import platform
from jnius import autoclass


class ImageSelector:
    def __init__(self, callback_handler):
        self.mActivity = None
        self.callback_handler = callback_handler

    def get_image(self, instance=None):
        self.mActivity = None
        if platform == "android":
            from android.permissions import request_permissions, Permission

            request_permissions(
                [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE]
            )
            from android import mActivity

            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            self.mActivity = mActivity
            intent = Intent(Intent.ACTION_PICK)
            intent.setType("image/*")
            self.mActivity.startActivityForResult(intent, 123)

            from android.activity import bind

            bind(on_activity_result=self.on_activity_result)
        else:
            # If the app is ran on desktop, use default image.
            self.callback_handler("./1.jpeg")

    def on_activity_result(self, request_code, result_code, data):
        if request_code == 123 and result_code == -1:
            uri = data.getData()
            print("Uri", uri)
            if self.mActivity:
                content_resolver = self.mActivity.getContentResolver()
                input_stream = content_resolver.openInputStream(uri)
                self.callback_handler(input_stream)
                return input_stream
            return None
        return None

