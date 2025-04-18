from picamera2 import Picamera2

picam2 = Picamera2()
#High-level API testing

# action = input("Choose service")

# if action == "capture":
#     picam2.start_and_capture("test.jpg")
# elif action == "record":
#     picam2.start_and_recording("test.mp4", duration=5)
# else:
#     print("Invalid action. again")

    

# picam2.start_and_capture("test.jpg")


picam2.start_and_record_video("test.mp4", duration=5)


