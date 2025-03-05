from kivy.core.text import Texture
from kivy.utils import platform
from kivymd.uix.card import MDCard
from jnius import autoclass, cast
from kivy.clock import Clock

if platform == "android":
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Context = autoclass("android.content.Context")
    CameraManager = autoclass("android.hardware.camera2.CameraManager")
    ImageReader = autoclass("android.graphics.ImageFormat")
    Activity = autoclass("android.app.Activity")
    Handler = autoclass("android.os.Handler")
    HandlerThread = autoclass("android.os.HandlerThread")


class AndroidCamera(MDCard):
    def __init__(self, **kwargs):
        super().__init__()

    def capture_image(self, instance):
        self.setup_camera()

    def setup_camera(self):
        activity = PythonActivity.mActivity
        context = cast(Context, activity.getApplicationContext())
        camera_manager = context.getSystemService(Context.CAMERA_SERVICE)
        camera_manager = cast(CameraManager, camera_manager)

        camera_ids = camera_manager.getCameraIdList()
        if not camera_ids:
            print("No cameras found")

        self.image_reader = ImageReader.newInstance(640, 480, ImageFormat.JPEG, 1)
        self.image_reader.setOnImageAvailableListener(self.on_image_available, None)

        handler_thread = HandlerThread("CameraBackground")
        handler_thread.start()
        handler = Handler(handler_thread.getLooper())
        camera_manager.openCamera(self.camera_id, self.camera_state_callback, handler)

    def on_image_available(self, reader):
        image = reader.acquireLatestImage()
        if image:
            buffer = image.getPlanes()[0].getBuffer()
            byte_array = bytearray(buffer.capacity())
            buffer.get(byte_array)
            self.image_data = bytes(byte_array)
            self.image.texture = self.bytes_to_texture(self.image_data)
            image.close()

    def bytes_to_texture(self, data):
        texture = Texture.create(size=(640, 480), colorfmt="rgb")
        texture.blit_buffer(data, colorfmt="rgb", bufferfmt="ubyte")
        return texture

    def camera_state_callback(self, camera, error):
        if error:
            print(f"Camera error: {error}")
            return

        # Create a capture session
        targets = [self.image_reader.getSurface()]
        session_state_callback = self.SessionStateCallback()
        camera.createCaptureSession(targets, session_state_callback, None)

    class SessionStateCallback(
        autoclass("android.hardware.camera2.CameraCaptureSession$StateCallback")
    ):
        def onConfigured(self, session):
            capture_request = session.getDevice().createCaptureRequest(
                autoclass(
                    "android.hardware.camera2.CameraDevice"
                ).TEMPLATE_STILL_CAPTURE
            )
            capture_request.addTarget(self.this.image_reader.getSurface())
            capture_request.set(
                autoclass("android.hardware.camera2.CaptureRequest").JPEG_ORIENTATION,
                90,
            )
            session.capture(capture_request.build(), None, None)

        def onConfigureFailed(self, session):
            print("Failed to configure camera session")
