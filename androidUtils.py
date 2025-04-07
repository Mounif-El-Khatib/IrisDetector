from kivy.utils import platform
from jnius import autoclass

try:
    from android.permissions import request_permissions, Permission
    from android import mActivity
except ImportError:
    # Handle non-Android platforms gracefully
    request_permissions = None
    Permission = None
    mActivity = None


class AndroidFilePicker:
    @staticmethod
    def get_image(app_instance, instance=None):
        """
        Initiates image selection on Android or uses a fallback for other platforms.
        :param app_instance: The calling app instance (e.g., IrisDetector).
        :param instance: Optional button instance for Kivy event handling.
        """
        if platform == "android" and mActivity:
            request_permissions(
                [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE]
            )

            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            app_instance.mActivity = mActivity  # Store the Android activity context
            intent = Intent(Intent.ACTION_PICK)
            intent.setType("image/*")

            try:
                app_instance.mActivity.startActivityForResult(intent, 123)
                from android.activity import bind

                bind(
                    on_activity_result=lambda req, res, data: AndroidFilePicker.on_activity_result(
                        req, res, data, app_instance
                    )
                )
            except Exception as e:
                print(f"Error starting image picker: {e}")
                if hasattr(app_instance, "resultLabel"):
                    app_instance.resultLabel.set_text(
                        "Error selecting image", Colors.SOFT_RED.value
                    )

    @staticmethod
    def on_activity_result(request_code, result_code, data, app_instance):
        """
        Handles the result of the Android image selection activity.
        :param request_code: Request code from the activity.
        :param result_code: Result code from the activity.
        :param data: Data returned from the activity.
        :param app_instance: The calling app instance.
        """
        if request_code == 123 and result_code == -1:
            uri = data.getData()
            print("Uri:", uri)
            if app_instance.mActivity:
                try:
                    content_resolver = app_instance.mActivity.getContentResolver()
                    input_stream = content_resolver.openInputStream(uri)
                    app_instance.handle_selection(input_stream)
                except Exception as e:
                    print(f"Error processing image URI: {e}")
