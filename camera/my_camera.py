import cv2
import numpy as np


class MyCamera:
    def __init__(self):
        self.cap = cv2.VideoCapture('/dev/video0')  # 1 is for Windows, 'dev/video0' is for Raspbian

        # Set the desired width and height
        self.width = 640
        self.height = 480

        # Set the camera resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

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
                    print(f"Ball at position: {center} with radius: {radius}")

        return image

    # Function for tracking all the ten cups in our image
    def track_cups(self, image):
        # Convert the image to HSV color space
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Define the range of white color in HSV
        white_upper_0 = np.array([130, 50, 150])
        white_lower_0 = np.array([0, 0, 50])

        # Different white range
        white_upper_1 = np.array([180, 100, 255])
        white_lower_1 = np.array([0, 0, 200])

        # Create masks for red color
        mask1 = cv2.inRange(hsv, white_lower_0, white_upper_0)
        mask2 = cv2.inRange(hsv, white_lower_1, white_upper_1)
        white_mask = cv2.bitwise_or(mask1, mask2)

        # Find contours in the red mask
        contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        min_radius = 100
        max_radius = 130

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
            return x, y, cup_radius  # Return the cup in which the ball is found
        return None

    # Function for processing an image with a certain function
    def process_frame(self, frame):
        frame = self.track_ball(frame)
        return frame

    # This is basically our main loop
    def run(self):
        while True:
            # Capture an image
            image = self.capture_image()
            if image is not None:
                # Track the ball in the image
                self.track_ball(image)

                # Track the cups in the image
                self.track_cups(image)

                for cup in self.cup_positions:
                    for center, radius in zip(self.ball_centers, self.ball_radii):
                        hit = self.check_ball_in_cup(center, radius, cup)

                        if hit is not None:
                            print(f"Ball is in cup at position: {hit[0], hit[1]} with radius: {hit[2]}")
                            break
                        else:
                            print("Ball is not in any cup.")

                # Display processed image
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
