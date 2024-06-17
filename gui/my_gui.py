import time
import customtkinter as ctk
import os


class MyGUI:
    def __init__(self, camera):
        self.name = None
        self.timer_id = None
        self.camera = camera
        self.cup_positions = None
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

        self.submit_button = ctk.CTkButton(self.root, text="Submit", command=self.start_game)
        self.submit_button.pack(pady=10)

        self.message_label = ctk.CTkLabel(self.root, text="", font=("Helvetica", 16))
        self.message_label.pack()

        self.score_label = ctk.CTkLabel(self.root, text=f"Score: {self.root_counter}", font=("Helvetica", 16))
        self.myentry.bind("<Return>", lambda event: self.start_game())

        self.reset_all_button = ctk.CTkButton(self.root, text="Reset All", command=self.reset_all)

        self.hit_cups = []  # Hier sind alle Cups, die aktuell getroffen wurden
        self.locked_cups = []  # Hier sind alle Cups, die bereits getroffen wurden

        self.start_time = None
        self.highscore_file = "highscores.txt"

        self.highscores = []
        self.load_highscores()
        self.highscore_label = None

    def draw_cups(self, scaled_cup_positions, cup_positions):
        self.canvas.delete("all")  # Löscht das Canvas vor dem Zeichnen
        self.score_label.configure(text=f"Score: {self.root_counter}")

        for cup in cup_positions:
            x, y, radius = cup

            if (x, y, radius) in self.hit_cups:
                color = "gray"
            else:
                color = "red"

            index = cup_positions.index(cup)

            x = scaled_cup_positions[index][0]
            y = scaled_cup_positions[index][1]
            radius = scaled_cup_positions[index][2]

            self.canvas.create_oval(
                x - radius, y - radius, x + radius, y + radius, fill=color, outline="black"
            )

    def start_game(self):
        name = self.myentry.get()
        if name:
            self.name = name
            self.myentry.pack_forget()
            self.submit_button.pack_forget()
            self.instruction_label.pack_forget()
            if self.highscore_label:
                self.highscore_label.pack_forget()
            self.message_label.configure(text=f"{name}")
            self.reset_all_button.pack(pady=10)
            self.score_label.pack(padx=20, pady=20)
            self.canvas.pack()
            self.start_time = time.time()
            self.update_timer()
            self.track_cups()  # Starte das Cup-Tracking hier

    def update_timer(self):
        if len(self.hit_cups) < len(self.cup_positions):
            elapsed_time = time.time() - self.start_time
            self.message_label.configure(text=f"Time: {elapsed_time:.2f} seconds")
            self.timer_id = self.root.after(100, self.update_timer)
        else:
            self.end_game()

    def end_game(self):
        elapsed_time = time.time() - self.start_time
        self.save_highscore(self.name, elapsed_time)
        self.load_highscores()
        self.root.after_cancel(self.timer_id)
        self.reset_game()
        self.reset_all()

    def save_highscore(self, name, time):
        with open(self.highscore_file, "a") as file:
            file.write(f"{name},{time:.2f}\n")

    def load_highscores(self):
        if not os.path.exists(self.highscore_file):
            with open(self.highscore_file, "w"):
                pass
        self.highscores = []
        with open(self.highscore_file, "r") as file:
            for line in file:
                name, time = line.strip().split(",")
                self.highscores.append((name, float(time)))
        self.highscores.sort(key=lambda x: x[1])
        self.display_highscores()

    def display_highscores(self):
        highscores_text = "Highscores:\n"
        for name, time in self.highscores:
            highscores_text += f"{name}: {time:.2f} seconds\n"
        if hasattr(self, 'highscore_label'):
            self.highscore_label.configure(text=highscores_text)
        else:
            self.highscore_label = ctk.CTkLabel(self.root, text=highscores_text, font=("Helvetica", 16))
            self.highscore_label.pack(pady=10)

    def display_message(self, message):
        self.message_label.configure(text=message)
        self.root.update()

    def reset_game(self):
        self.name = None
        self.root_counter = 0
        self.score_label.configure(text=f"Score: {self.root_counter}")
        self.canvas.delete("all")
        self.message_label.configure(text="")
        self.hit_cups = []
        self.locked_cups = []

    def reset_all(self):
        self.reset_game()
        self.root.after_cancel(self.timer_id)
        self.message_label.configure(text="Input your name:")
        self.myentry.delete(0, "end")
        self.myentry.pack()
        self.submit_button.pack(pady=10)
        self.reset_all_button.pack_forget()
        self.score_label.pack_forget()
        self.canvas.pack_forget()
        self.display_highscores()

    def track_cups(self):
        while True:
            self.hit_cups = []

            scaled_cup_positions = self.camera.scale_positions(camera_resolution=(1024, 1024),
                                                               gui_size=(self.canvas_width, self.canvas_height))

            for cup in self.cup_positions:
                for center, radius in zip(self.camera.ball_centers, self.camera.ball_radii):
                    hit_cup = self.camera.check_ball_in_cup(center, radius, cup)

                    if hit_cup and hit_cup not in self.hit_cups:
                        self.hit_cups.append(hit_cup)

            self.draw_cups(scaled_cup_positions, self.cup_positions)

            # Berechne den aktuellen Score
            if self.hit_cups:
                self.root_counter = len(self.hit_cups)
                self.score_label.configure(text=f"Score: {self.root_counter}")

            if not self.hit_cups:
                self.root_counter = 0
                self.score_label.configure(text=f"Score: {self.root_counter}")

            self.root.update()

            # Überprüfe, ob alle Cups getroffen wurden
            if len(self.hit_cups) == len(self.cup_positions):
                self.display_message("You have won the game!")
                time.sleep(2)
                self.end_game()
                break
