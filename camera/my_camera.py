import cv2

import numpy as np


class MyCamera:
    def __init__(self):
        self.cap = cv2.VideoCapture(1)

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

        self.prev_center = None
        self.exit_direction = None
        self.last_known_position = None
        self.last_known_direction = None

        self.cup_positions = []  # Set the positions of the cups here

        self.ball_center = None
        self.ball_radius = None

    # Function for recording an image and converting it to an array
    def capture_image(self):
        if not self.cap.isOpened():
            print("Error: Unable to open camera.")
            self.cap.open('/dev/video0')
            print("Camera opened successfully.")

        ret, frame = self.cap.read()
        cv2.flip(frame, 0, frame)
        if ret:
            return frame
        else:
            print("Unable to capture an image.")
            return None

    # Function to find the brightest pixel in an image
    def track_brightest_pixel(self, image):
        # Convert the image to grayscale
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Find the brightest pixel in the image
        _, max_val, _, max_loc = cv2.minMaxLoc(gray_image)

        return max_loc, max_val

    # Function to track the brightest object in an image
    def track_brightest_object(self, image):
        # Convert the image to grayscale
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresholded_image = cv2.threshold(gray_image, 185, 255, cv2.THRESH_BINARY)
        # Find contours in the thresholded image
        contours, _ = cv2.findContours(thresholded_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # Filter contours based on area
        filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 100]
        # Draw rectangles around filtered contours
        for contour in filtered_contours:
            # Draw rectangles around contours
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        return image

    # This function is for ball segmentation and tracking
    def track_ball(self, image):

        # Make the same for debug reasons but in a red color
        red_upper = np.array([180, 255, 255])
        red_lower = np.array([160, 100, 100])

        # Resize, blur and convert the image to HSV
        blurred = cv2.GaussianBlur(image, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # Use masks to segment the white color
        mask = cv2.inRange(hsv, red_lower, red_upper)
        mask = cv2.erode(mask, None, iterations=1)
        mask = cv2.dilate(mask, None, iterations=1)

        contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        center = None

        # If at least one contour is found
        if len(contours) > 0:
            # Find the largest contour in the mask
            # Then use it to compute the minimum enclosing circle and centroid
            c = max(contours, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

            # self.detect_ball_direction(image, self.prev_center, center)

            if radius > 10:
                # Draw the circle and centroid on the frame
                cv2.circle(image, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                cv2.circle(image, center, 5, (0, 0, 255), -1)

                self.ball_radius = radius
                self.ball_center = center

            # Update the previous center
            self.prev_center = center

        return image

    # Function to check if ball is in any cup
    def check_ball_in_cup(self, ball_center, ball_radius, cups_positions):
        if ball_center is None:
            return None
        for (x, y, cup_radius) in cups_positions:
            distance = np.sqrt((ball_center[0] - x) ** 2 + (ball_center[1] - y) ** 2)
            if distance < cup_radius - ball_radius:
                return x, y, cup_radius  # Return the cup in which the ball is found
        return None

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
        red_mask = cv2.bitwise_or(mask1, mask2)

        # Find contours in the red mask
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        min_radius = 50
        max_radius = 130

        cups = []
        for contour in contours:
            # Filter small contours that are not cups
            if cv2.contourArea(contour) > 500:
                # Get the minimum enclosing circle
                ((x, y), radius) = cv2.minEnclosingCircle(contour)
                if min_radius < radius < max_radius:
                    cups.append((int(x), int(y), int(radius)))
                    self.cup_positions.append(cups)
                    # Draw the circle around the cup
                    cv2.circle(image, (int(x), int(y)), int(radius), (0, 255, 0), 2)

        for cup in cups:
            print(f"Cup at position: {cup[0], cup[1]} with radius: {cup[2]}")
        return image, cups

    # Function for processing an image with a certain function
    def process_frame(self, frame):
        processed_frame = self.track_ball(frame)
        return processed_frame

    # This is basically our main loop
    def run(self):
        while True:
            # Capture an image
            image = self.capture_image()
            if image is not None:
                # Get processed image from the future
                processed_image = self.process_frame(image)

                # Track the cups in the processed image
                self.track_cups(processed_image)

                for cup in self.cup_positions:
                    hit = self.check_ball_in_cup(self.ball_center, self.ball_radius, cup)

                    if hit is not None:
                        print(f"Ball is in cup at position: {hit[0], hit[1]} with radius: {hit[2]}")
                        break
                    else:
                        print("Ball is not in any cup.")

                # Display processed image
                cv2.imshow("Processed Image", processed_image)

                if self.last_known_position is not None:
                    print("Last known position:", self.last_known_position)
                    print("Last known direction:", self.last_known_direction)

                if self.exit_direction is not None:
                    print("Exit direction:", self.exit_direction)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                print("Failed to capture an image.")
                break

    cv2.destroyAllWindows()

    # Function for detecting the cups in the image
    def detect_cups(self):
        pass

    # Destructor method to release the camera when the object is destroyed
    def __del__(self):
        if self.cap.isOpened():
            self.cap.release()
