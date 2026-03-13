import camera

# Initialize camera (safe version)
camera_init_ok = False
try:
    # Some devices need resolution/params to avoid init failure
    camera.init(0, format=camera.JPEG, framesize=camera.FRAME_VGA)  # 640x480
    camera_init_ok = True
except Exception as e:
    print(f"Camera init failed: {type(e)} | {str(e)}")  # Print error type + msg
    if camera_init_ok:
        camera.deinit()  # Only deinit if init success

# Capture photo only if camera init ok
if camera_init_ok:
    try:
        buf = camera.capture()  # Capture image data
        # Save to file (ASCII filename, avoid encoding issue)
        with open("second_image.jpg", "wb") as f:
            f.write(buf)
        print("Photo saved successfully, download in Thonny")
    except Exception as e:
        # Print detailed exception info (type + message)
        print(f"Capture/save failed: {type(e)} | {str(e)}")
    finally:
        # Ensure camera release (fix spelling: deinit())
        camera.deinit()
else:
    print("Camera init failed, exit")