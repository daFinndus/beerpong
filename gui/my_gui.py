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

        self.hit_cups = []

    def draw_cups(self, cup_positions):
        self.canvas.delete("all")  # Clear the canvas before drawing

        for cup in cup_positions:
            x, y, radius = cup

            print(f"Comparing cup at position: {x, y, radius} with hit_cups: {self.hit_cups}")

            if (x, y, radius) in self.hit_cups:
                print(f"Cup at position: {x, y} with radius: {radius} is in the hit_cups list!")
                self.root_counter = len(self.hit_cups)
                self.score_label.configure(text=f"Score: {self.root_counter}")
                color = "gray"
            else:
                color = "red"

            self.canvas.create_oval(
                x - radius, y - radius, x + radius, y + radius, fill=color, outline="black"
            )

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
            self.canvas.pack()

    def reset_game(self):
        if self.click_counter == 10:
            self.root.counter = 0
            self.score_label.configure(text=f"Score: {self.root.counter}")
            self.click_counter = 0
            self.num_circles = 8
            self.canvas.delete("all")

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

    def run(self, camera):
        self.hit_cups = []

        while True:
            scaled_cup_positions = camera.scale_positions(camera_resolution=(640, 480),
                                                          gui_size=(self.canvas_width, self.canvas_height))

            for cup in camera.cup_positions:
                for center, radius in zip(camera.ball_centers, camera.ball_radii):
                    hit_cup = camera.check_ball_in_cup(center, radius, cup)

                    if hit_cup and hit_cup not in self.hit_cups:
                        self.hit_cups.append(hit_cup)

            self.draw_cups(camera.cup_positions)
            self.root.update()
