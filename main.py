import gui.my_gui
import camera.my_camera

from threading import Thread

if __name__ == "__main__":
    camera = camera.my_camera.MyCamera()

    if camera is not None:
        gui = gui.my_gui.MyGUI(camera)
    else:
        print("Failed to initialize camera.")
        exit()

    camera_thread = Thread(target=camera.run)

    camera_thread.start()
    gui.run()
