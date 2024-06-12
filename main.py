import gui.my_gui
import camera.my_camera

from threading import Thread

if __name__ == "__main__":
    camera = camera.my_camera.MyCamera()
    if camera.open_camera():
        gui = gui.my_gui.MyGUI()
        gui.run(camera)
    else:
        print("Could not open camera. Exiting.")

    camera_thread = Thread(target=camera.run)

    camera_thread.start()
