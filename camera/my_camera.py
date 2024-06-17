import cv2
import numpy as np
import time


class MyCamera:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(1)  # .VideoCapture(1) is for Windows, .VideoCapture(/dev/video0) is for Raspbian

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print("Camera resolution: {}x{}".format(self.width, self.height))

        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))

        # Turn off auto white balance and auto exposure
        self.cap.set(cv2.CAP_PROP_AUTO_WB, 0)
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
        self.cap.set(cv2.CAP_PROP_EXPOSURE, -6.0)

        # Following variables are used for tracking the balls
        self.ball_centers = []
        self.ball_radii = []

        self.cup_positions = []  # Set the positions of the cups here
        self.initial_image = None

    def open_camera(self):
        if not cv2.VideoCapture(self.camera_index).isOpened():
            print(f"Camera with index {self.camera_index} is not available.")
            return False
        self.cap = cv2.VideoCapture(self.camera_index)
        return True

    # Function for recording an image and converting it to an array
    def capture_image(self):
        if not self.cap.isOpened():
            print("Error: Unable to open camera.")
            self.cap.open('/dev/video0')  # .open(1) is for Windows, .open(/dev/video0) is for Raspbian
            print("Camera opened successfully.")

        ret, frame = self.cap.read()

        if ret:
            return frame
        else:
            print("Unable to capture an image.")
            return None

    # This function is for ball segmentation and tracking
    def track_ball(self, image):
        # Make the same for debug reasons but in a red color
        orange_lower = np.array([5, 150, 150])
        orange_upper = np.array([15, 255, 255])

        # Resize, blur and convert the image to HSV
        blurred = cv2.GaussianBlur(image, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # Use masks to segment the white color
        mask = cv2.inRange(hsv, orange_lower, orange_upper)
        mask = cv2.erode(mask, None, iterations=1)
        mask = cv2.dilate(mask, None, iterations=1)

        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        self.ball_centers = []
        self.ball_radii = []

        # If contours is not empty
        if contours:
            for c in contours:
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                if M["m00"] > 0:
                    center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                else:
                    center = None

                if radius > 10:
                    # Draw the circle and centroid on the frame
                    cv2.circle(image, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                    if center:
                        cv2.circle(image, center, 5, (0, 0, 255), -1)

                    self.ball_centers.append(center)
                    self.ball_radii.append(radius)

        return image

    # Function for tracking all the ten cups in our image
    def track_cups(self, image):
        # Convert the image to HSV color space
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Adjusted white ranges for better detection in lower light conditions
        white_lower_0 = np.array([0, 0, 150])
        white_upper_0 = np.array([180, 30, 255])

        white_lower_1 = np.array([0, 0, 200])
        white_upper_1 = np.array([180, 50, 255])

        # Create masks for red color
        mask1 = cv2.inRange(hsv, white_lower_0, white_upper_0)
        mask2 = cv2.inRange(hsv, white_lower_1, white_upper_1)
        white_mask = cv2.bitwise_or(mask1, mask2)

        white_mask = cv2.erode(white_mask, None, iterations=2)
        white_mask = cv2.dilate(white_mask, None, iterations=2)
        white_mask = cv2.GaussianBlur(white_mask, (5, 5), 0)

        contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        min_radius = 80
        max_radius = 110

        # Store cups with their positions in our list
        cups = [(int(x), int(y), int(radius)) for cnt in contours if cv2.contourArea(cnt) > 500 for ((x, y), radius) in
                [cv2.minEnclosingCircle(cnt)] if min_radius < radius < max_radius]

        for cup in cups:
            cv2.circle(image, (cup[0], cup[1]), cup[2], (0, 255, 0), 2)
            print(f"Cup at position: {cup[0], cup[1]} with radius: {cup[2]}")

        self.cup_positions = cups
        return image, cups

    # Function to check if ball is in any cup
    def check_ball_in_cup(self, ball_center, ball_radius, cup):
        if ball_center is None:
            return None

        # Unpack our cup information
        (x, y, cup_radius) = cup

        # Calculate if our ball is in the cup
        distance = np.sqrt((ball_center[0] - x) ** 2 + (ball_center[1] - y) ** 2)

        # If the distance is less than the radius of the cup minus the radius of the ball
        if distance < cup_radius - ball_radius:
            return x, y, cup_radius
        return None

    # Function for processing an image with a certain function
    def process_frame(self, frame):
        frame = self.track_ball(frame)
        return frame

    def scale_positions(self, camera_resolution, gui_size):
        scaled_positions = []
        for cup in self.cup_positions:
            x, y, radius = cup
            scaled_x = int(x * gui_size[0] / camera_resolution[0])
            scaled_y = int(y * gui_size[1] / camera_resolution[1])
            scaled_radius = int(radius * min(gui_size[0] / camera_resolution[0], gui_size[1] / camera_resolution[1]))
            scaled_positions.append((scaled_x, scaled_y, scaled_radius))
        return scaled_positions

    # This is basically our main loop
    def run(self):
        print("Taking initial photo to detect cups...")
        self.initial_image = self.capture_image()
        if self.initial_image is not None:
            _, cups = self.track_cups(self.initial_image)
            print(f"Detected cups: {cups}")

            start_time = time.time()
            while time.time() - start_time < 5:
                try:
                    cv2.imshow("Initial Image", self.initial_image)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                except Exception as e:
                    print(f"Error displaying initial image: {e}")

        while True:
            # Capture an image
            image = self.capture_image()
            if image is not None:
                # Track the ball in the image
                self.track_ball(image)

                # Draw a circle around each cup
                for cup in self.cup_positions:
                    cv2.circle(image, (cup[0], cup[1]), cup[2], (0, 255, 0), 2)
                    print(f"Cup at position: {cup[0], cup[1]} with radius: {cup[2]}")

                try:
                    cv2.imshow("Image", image)
                except Exception as e:
                    print(f"Error displaying image: {e}")

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            else:
                print("Failed to capture an image.")
                break

        cv2.destroyAllWindows()

    # Destructor method to release the camera and destroy the windows
    def __del__(self):
        if self.cap.isOpened():
            self.cap.release()
            cv2.destroyAllWindows()
            print("Camera released and windows destroyed.")
