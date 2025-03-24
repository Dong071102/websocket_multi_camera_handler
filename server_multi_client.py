import asyncio
import json
import cv2
import base64
import numpy as np
from datetime import datetime
from websockets.server import serve  # ✅ Corrected import

# Define cameras and their URLs
camera_urls = {
    "cam_1": "rtsp://rtspstream:cpRarbk7RpY2MFvAadAwn@zephyr.rtsp.stream/movie",
   "cam_2": "rtsp://rtspstream:cpRarbk7RpY2MFvAadAwn@zephyr.rtsp.stream/traffic",
    "cam_3": "http://192.168.0.100:81/stream",
    "cam_4": "rtsp://your_camera_4_url",
    "cam_5": "rtsp://your_camera_5_url",
}

async def capture_and_send_video(websocket, camera_url):
    """Capture video from a specific camera and send frames to connected clients."""
    cap = cv2.VideoCapture(camera_url)

    if not cap.isOpened():
        await websocket.send(json.dumps({
            "type": "error",
            "message": f"Failed to connect to camera: {camera_url}",
            "timestamp": datetime.now().isoformat()
        }))
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (640, 480))  # Resize for efficiency
            _, buffer = cv2.imencode('.jpg', frame)
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')

            # Send frame as JSON
            message = json.dumps({
                "type": "video_frame",
                "frame": jpg_as_text,
                "timestamp": datetime.now().isoformat()
            })

            await websocket.send(message)
            await asyncio.sleep(1/30)  # 30 FPS

    except websockets.ConnectionClosed:
        pass
    finally:
        cap.release()

async def handle_client(websocket, path):
    """Handle a client connection and stream video from the assigned camera."""
    camera_id = path.lstrip("/")  # Extract camera identifier

    if camera_id in camera_urls:
        camera_url = camera_urls[camera_id]
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Connected to WebSocket server - Streaming {camera_id}",
            "timestamp": datetime.now().isoformat()
        }))
        await capture_and_send_video(websocket, camera_url)
    else:
        await websocket.send(json.dumps({
            "type": "error",
            "message": "Invalid camera endpoint",
            "timestamp": datetime.now().isoformat()
        }))
        await websocket.close()

async def main():
    """Start WebSocket server for multiple cameras."""
    HOST = "localhost"
    PORT = 8765

    # ✅ FIX: Use `serve` from `websockets.server`
    server = await serve(handle_client, HOST, PORT)
    print(f"WebSocket server started at ws://{HOST}:{PORT}")
    print("Available camera paths:", list(camera_urls.keys()))

    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
