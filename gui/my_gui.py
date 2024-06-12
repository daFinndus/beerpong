import customtkinter as ctk

from camera.my_camera import MyCamera


class MyGUI:
    def __init__(self):
        self.radius = 15
        self.gap = 5
        self.root = ctk.CTk()
        self.root.geometry("500x1000")
        self.root.title("Beerpong")

        self.label = ctk.CTkLabel(self.root, text="Beerpong", font=("Arial", 24))
        self.label.pack(padx=20, pady=20)

        self.root_counter = 0
        self.click_counter = 0
        self.num_circles = 8
        self.canvas_width = 500
        self.canvas_height = 500
        self.canvas = ctk.CTkCanvas(self.root, width=self.canvas_width, height=self.canvas_height)
        self.canvas.configure(bg="black")

        self.instruction_label = ctk.CTkLabel(self.root, text="Input your name:")
        self.instruction_label.pack(pady=10)

        self.myentry = ctk.CTkEntry(self.root, font=("Arial", 16))
        self.myentry.pack()

        self.submit_button = ctk.CTkButton(self.root, text="Submit", command=self.display_name)
        self.submit_button.pack(pady=10)

        self.message_label = ctk.CTkLabel(self.root, text="", font=("Helvetica", 16))
        self.message_label.pack()

        self.score_label = ctk.CTkLabel(self.root, text=f"Score: {self.root_counter}", font=("Helvetica", 16))
        self.myentry.bind("<Return>", lambda event: self.display_name())

        self.reset_game_button = ctk.CTkButton(self.root, text="Reset Score", command=self.reset_game)

        self.reset_all_button = ctk.CTkButton(self.root, text="Reset All", command=self.reset_all)

    def draw_cups(self, cup_positions):
        for cup in cup_positions:
            x, y, radius = cup
            self.canvas.create_oval(
                x - radius, y - radius, x + radius, y + radius, fill="red", outline="black"
            )

    """
    def circle_clicked(self, event):
        item = self.canvas.find_closest(event.x, event.y)[0]
        self.canvas.itemconfigure(item, fill="gray")
        self.root.counter += 1
        self.score_label.configure(text=f"Score: {self.root.counter}")
        self.click_counter += 1
        if self.click_counter == 4:
            self.num_circles = 6
            self.redraw_pyramid()
        elif self.click_counter == 7:
            self.num_circles = 3
            self.redraw_pyramid()
        elif self.click_counter == 9:
            self.num_circles = 1
            self.redraw_pyramid()
        elif self.click_counter == 10:
            self.canvas.delete("all")
            self.canvas.create_text(self.canvas_width // 2, self.canvas_height // 2,
                                    text="Congratulations! You won!", font=("Arial", 24), fill="white")
    """

    """
    def redraw_pyramid(self):
        self.canvas.delete("all")
        if self.click_counter == 4:
            self.num_circles = 6
        elif self.click_counter == 7:
            self.num_circles = 3
        elif self.click_counter == 9:
            self.num_circles = 1
        self.draw_pyramid()
    """

    def display_name(self):
        name = self.myentry.get()
        if name:
            self.myentry.pack_forget()
            self.submit_button.pack_forget()
            self.instruction_label.pack_forget()
            self.message_label.configure(text=f"{name}")
            self.reset_game_button.pack(pady=10)
            self.reset_all_button.pack(pady=10)
            self.score_label.pack(padx=20, pady=20)
            # self.draw_pyramid()
            self.canvas.pack()

    """
    def draw_pyramid(self):
        x0 = self.canvas_width // 2 - (self.radius * (self.num_circles / 2))
        y0 = self.canvas_height // 2
        rows = (self.num_circles + 1) // 2
        for i in range(rows):
            for j in range(i + 1):
                circle = self.canvas.create_oval(
                    x0 + j * (2 * self.radius + self.gap) + (rows - i - 1) * (self.radius + self.gap),  # x-Koordinate
                    y0 - i * (2 * self.radius + self.gap),  # y-Koordinate
                    x0 + j * (2 * self.radius + self.gap) + 2 * self.radius + (rows - i - 1) * (self.radius + self.gap),
                    # x-Koordinate + Durchmesser
                    y0 - i * (2 * self.radius + self.gap) + 2 * self.radius,  # y-Koordinate + Durchmesser
                    fill="red", outline="black"
                )
                self.canvas.tag_bind(circle, '<Button-1>',
                                     lambda e: self.circle_clicked(e))  # Mausklick-Ereignis binden
    """

    def reset_game(self):
        if self.click_counter == 10:
            self.root.counter = 0
            self.score_label.configure(text=f"Score: {self.root.counter}")
            self.click_counter = 0
            self.num_circles = 8
            self.canvas.delete("all")
            "self.draw_pyramid()"

    def reset_all(self):
        self.reset_game()
        self.message_label.configure(text="Input your name:")
        self.myentry.delete(0, "end")
        self.myentry.pack()
        self.submit_button.pack(pady=10)
        self.reset_game_button.pack_forget()
        self.reset_all_button.pack_forget()
        self.score_label.pack_forget()
        self.canvas.pack_forget()

    """
    def run(self):
        self.root.mainloop()
    """

    def gray_out_cup(self, cup_position):
        x, y, radius = cup_position
        self.canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius, fill="gray", outline="black"
        )
        self.root_counter += 1
        self.score_label.configure(text=f"Score: {self.root_counter}")

    def run(self, camera):
        hit_cup = None

        while True:
            camera.get_cup_positions()
            scaled_cup_positions = camera.scale_positions(camera_resolution=(640, 480),
                                                          gui_size=(self.canvas_width, self.canvas_height))
            self.draw_cups(scaled_cup_positions)
            for cup in camera.cup_positions:
                for center, radius in zip(camera.ball_centers, camera.ball_radii):
                    hit_cup = camera.check_ball_in_cup(center, radius, cup)

            if hit_cup:
                self.gray_out_cup(hit_cup)
            self.root.update()


if __name__ == "__main__":
    camera = MyCamera()
    if camera.open_camera():
        gui = MyGUI()
        gui.run(camera)
    else:
        print("Could not open camera. Exiting.")
