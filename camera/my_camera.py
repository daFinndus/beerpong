import cv2
import numpy as np


class MyCamera:
    def __init__(self):
        self.cap = cv2.VideoCapture(1)  # .VideoCapture(1) is for Windows, .VideoCapture(/dev/video0) is for Raspbian

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
        self.cap.set(cv2.CAP_PROP_EXPOSURE, -7.0)

        # Following variables are used for tracking the ball
        self.prev_center = None
        self.ball_center = None
        self.ball_radius = None

        self.cup_positions = []  # Set the positions of the cups here

        cv2.namedWindow('Image')

        self.brightness = 50
        self.contrast = 50

        # Create trackbars for adjusting brightness and contrast
        cv2.createTrackbar('Brightness', 'Image', self.brightness, 100, self.on_trackbar_brightness)
        cv2.createTrackbar('Contrast', 'Image', self.contrast, 100, self.on_trackbar_contrast)

    # Function for trackbar
    def on_trackbar_brightness(self, x):
        self.brightness = cv2.getTrackbarPos('Brightness', 'Image') - 50
        print(f"Brightness: {self.brightness}")

    # Function for trackbar
    def on_trackbar_contrast(self, x):
        self.contrast = cv2.getTrackbarPos('Contrast', 'Image') - 50
        print(f"Contrast: {self.contrast}")

    # Function for adjusting the brightness and contrast of an image
    def adjust_brightness_contrast(self, image):
        adjusted = cv2.convertScaleAbs(image, alpha=1 + self.contrast / 50.0, beta=self.brightness)
        return adjusted

    # Function for recording an image and converting it to an array
    def capture_image(self):
        if not self.cap.isOpened():
            print("Error: Unable to open camera.")
            self.cap.open(1)  # .open(1) is for Windows, .open(/dev/video0) is for Raspbian
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

        # If contours is not empty
        if contours:
            # Find the largest contour in the mask
            # Then use it to compute the minimum enclosing circle and centroid
            c = max(contours, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

            if radius > 10:
                # Draw the circle and centroid on the frame
                cv2.circle(image, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                cv2.circle(image, center, 5, (0, 0, 255), -1)

                self.ball_radius = radius
                self.ball_center = center
                print(f"Ball at position: {center} with radius: {radius}")

            # Update the previous center
            self.prev_center = center

        return image

    # Function for tracking all the ten cups in our image
    def track_cups(self, image):
        # Convert the image to HSV color space
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Define the range of white color in HSV
        white_upper_0 = np.array([130, 100, 255])
        white_lower_0 = np.array([0, 0, 150])

        # Different white range
        white_upper_1 = np.array([180, 255, 255])
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
        print("Going to process the frame.")
        frame = self.adjust_brightness_contrast(frame)
        print("Brightness and contrast adjusted.")
        frame = self.track_ball(frame)
        print("Ball tracked.")
        return frame

    # This is basically our main loop
    def run(self):
        while True:
            # Capture an image
            image = self.capture_image()
            if image is not None:
                print("Image captured.")
                # Get processed image from the future
                processed_image = self.process_frame(image)
                print("Frame processed.")

                # Track the cups in the processed image
                self.track_cups(processed_image)
                print("Cups tracked.")

                for cup in self.cup_positions:
                    print("Got cup: ", cup)
                    hit = self.check_ball_in_cup(self.ball_center, self.ball_radius, cup)

                    if hit is not None:
                        print(f"Ball is in cup at position: {hit[0], hit[1]} with radius: {hit[2]}")
                        break
                    else:
                        print("Ball is not in any cup.")

                        # Display processed image
                        try:
                            cv2.imshow("Image", processed_image)
                            print("Image displayed.")
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
