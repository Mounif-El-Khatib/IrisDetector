from kivy.utils import platform


class Snackbar:

    def __init__(self):
        self.toast = None
        if platform == "android":
            try:
                from jnius import autoclass

                self.PythonActivity = autoclass("org.kivy.android.PythonActivity")
                self.Toast = autoclass("android.widget.Toast")
                self.String = autoclass("java.lang.String")
            except Exception as e:
                print(f"Error initializing Toast: {e}")

    def show(self, message, duration="short"):
        if platform == "android" and self.Toast:
            try:
                context = self.PythonActivity.mActivity
                java_message = self.String(str(message))

                length = (
                    self.Toast.LENGTH_SHORT
                    if duration == "short"
                    else self.Toast.LENGTH_LONG
                )

                def show_toast():
                    self.toast = self.Toast.makeText(context, java_message, length)
                    self.toast.show()

                context.runOnUiThread(show_toast)

            except Exception as e:
                print(f"Error showing Toast: {e}")
