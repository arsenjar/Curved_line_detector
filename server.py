import cv2
import threading
from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from LineDetector import LineDetector

app = Flask(__name__)
CORS(app)

# --- Configuration ---
HOST_IP = '0.0.0.0'
PORT = 8080
# The source stream
STREAM_URL = "http://192.168.240.150:8080/video_feed"

# --- Global Variables ---
line_detector = LineDetector()  # Note: Use lowercase for instance
last_frame = None
lock = threading.Lock()  # Prevents threads from reading while the buffer is updating


def update_camera():
    """Background thread to constantly fetch the latest frame."""
    global last_frame
    cap = cv2.VideoCapture(STREAM_URL)

    while True:
        success, frame = cap.read()
        if not success:
            print("Lost connection to camera. Reconnecting...")
            cap.release()
            cv2.waitKey(2000)  # Wait 2 seconds before retry
            cap = cv2.VideoCapture(STREAM_URL)
            continue

        with lock:
            last_frame = frame.copy()


# Start the background camera thread immediately
cam_thread = threading.Thread(target=update_camera, daemon=True)
cam_thread.start()


def generate_frames(processed=False):
    while True:
        with lock:
            if last_frame is None:
                continue
            frame = last_frame.copy()

        if processed:
            frame = line_detector.process_frame(frame)
            print("Frame processed")
            # except Exception as e:
            #     pass  # Fallback to raw frame if processing fails

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(processed=False),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_feed/processed')
def video_feed_processed():
    return Response(generate_frames(processed=True),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/control/set', methods=['POST'])
def control_set():
    global current_state

    try:
        data = request.get_json()
        current_state.update(data)

        print(f"Received Command: {current_state['command']}, State: {data}")
        return jsonify({'status': 'success', 'state': current_state})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


if __name__ == '__main__':
    # Using threaded=True is okay now because they don't fight over the camera object
    app.run(host=HOST_IP, port=PORT, threaded=True)