import gui.my_gui
import camera.my_camera

from threading import Thread

if __name__ == "__main__":
    camera = camera.my_camera.MyCamera()
    gui = gui.my_gui.MyGUI()

    camera_thread = Thread(target=camera.run)

    camera_thread.start()
    gui.run(camera)
