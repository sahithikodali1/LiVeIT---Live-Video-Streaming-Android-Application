#import libraries/packages required
import socket
import numpy as np
import cv2
import pickle
import tkinter as tk
from tkinter import Button

class VideoClient:
    def __init__(self, master):

        # Initialize the VideoClient object
        self.master = master
        self.master.title("Video Client")
        self.server_ip = "10.0.0.155"  # Replace with the actual IP address of the server machine
        self.server_port = 6666

        # Create a video capture object and set resolution
        self.cap = cv2.VideoCapture(0) #chnage index as needed for camera access
        self.cap.set(3, 640)
        self.cap.set(4, 480)

        # Create Start Stream button
        self.start_button = Button(self.master, text="Start Stream", command=self.start_stream)
        self.start_button.pack(pady=10)

        # Create Stop Stream button and initially disable it
        self.stop_button = Button(self.master, text="Stop Stream", command=self.stop_stream)
        self.stop_button.pack(pady=10)
        self.stop_button['state'] = 'disabled'  # Disable stop button initially

        # Flag to track if streaming is active
        self.streaming = False

    def start_stream(self):
        # Disable Start button, enable Stop button, set streaming flag, and initialize socket for streaming
        self.start_button['state'] = 'disabled'
        self.stop_button['state'] = 'normal'
        self.streaming = True

        # Create a UDP socket for streaming
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1000000)
        
        # Start updating the GUI
        self.update_gui()
    
    def update_gui(self):

        # Check if streaming is active
        if self.streaming:

            # Read a frame from the camera
            ret, img = self.cap.read()

            # Display the image
            cv2.imshow('Image Client', img)

            # Encode the frame and send it to the server
            ret, buffer = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 30])
            x_as_bytes = pickle.dumps(buffer)
            self.s.sendto(x_as_bytes, (self.server_ip, self.server_port))

            # Check for key presses
            if cv2.waitKey(1) & 0xFF == 32: #check for space key
                print('Streaming paused')
                self.start_button['state'] = 'normal'
                self.stop_button['state'] = 'disabled'
                return

            if cv2.waitKey(1) & 0xFF == 27: #check for esc key
                print('Streaming stopped')
                self.streaming = False
                self.stop_stream()
                return
            
            # Schedule the next update after 10 milliseconds
            self.master.after(10, self.update_gui)

        else:
            # Release resources when streaming is stopped
            self.cap.release()
            cv2.destroyAllWindows()
            self.s.close()
            
            # Enable Start button and disable Stop button
            self.start_button['state'] = 'normal'
            self.stop_button['state'] = 'disabled'

    def stop_stream(self):

        # Send stop signal to the server, stop streaming, and release resources
        self.s.sendto(b'stop', (self.server_ip, self.server_port))
        print('Streaming stopped')
        self.streaming = False

        self.start_button['state'] = 'normal'
        self.stop_button['state'] = 'disabled'

        self.cap.release()
        cv2.destroyAllWindows()
        self.s.close()

## Main function that calls the app to run
if __name__ == "__main__":

    # Create a Tkinter root window and instantiate the VideoClient
    root = tk.Tk()
    client = VideoClient(root)
    root.mainloop()
