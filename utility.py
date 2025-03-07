import numpy as np
import cv2


def preprocess_image(frame):
    if frame is None:
        return None
    frame = frame.astype(np.float32)
    frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)
    frame = frame.astype(np.uint8)
    if len(frame.shape) == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    elif frame.shape[2] == 4:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    return frame


def byte_array_to_frame(input_source):
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
    return frame
