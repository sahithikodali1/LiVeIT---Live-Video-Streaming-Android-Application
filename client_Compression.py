#import libraries/packages required
import socket
import cv2
import pickle
import time
import numpy as np
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.graphics.texture import Texture
from kivy.clock import Clock
import zlib


class VideoClientApp(App):
    def build(self):

        # Initialize variables
        self.server_ip = None
        self.server_port = 6666

        self.streaming = False
        self.sent_time = 0

        # UI layout setup
        layout = BoxLayout(orientation='vertical')

        self.server_ip_input = TextInput(multiline=False, hint_text="Enter Server IP Address")
        layout.add_widget(self.server_ip_input)

        self.image = Image()
        layout.add_widget(self.image)

        self.camera = Camera(resolution=(640, 480), play=False)
        self.camera.bind(on_texture=self.update_texture)
        layout.add_widget(self.camera)

        self.start_button = Button(text="Start Stream")
        self.start_button.bind(on_press=self.start_stream)
        layout.add_widget(self.start_button)

        self.stop_button = Button(text="Stop Stream", on_press=self.stop_stream, state='normal', disabled=True)
        layout.add_widget(self.stop_button)
        
        # Performance metrics variables
        self.sent_frames = 0
        self.received_frames = 0
        self.latency_list = []
        self.data_sent_list = []
        self.nocomp_data_sent_list = []

        # Update UI at 30 FPS
        Clock.schedule_interval(self.update, 1.0 / 30.0)  # Update at 30 FPS

        return layout

    ## Method to start video streaming
    def start_stream(self, instance):

        # Get server IP from TextInput
        self.server_ip = self.server_ip_input.text.strip()
        if not self.server_ip:
            print("Please enter a valid server IP address.")
            return
        
        # Disable start button, enable stop button, and set streaming flag
        self.start_button.disabled = True
        self.stop_button.disabled = False
        self.streaming = True

        # Create a UDP socket for streaming
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1000000)

        # Start the camera
        self.camera.play = True


    ## Methods to update GUI and send data for each captured frame
    def update_texture(self, instance, texture):
        # Trigger the update method when a new frame is available
        if self.streaming:
            Clock.schedule_once(self.update)

    def update(self, dt):
        if self.streaming and self.camera.texture is not None:
            # Convert the texture pixels to a numpy array
            pixels = np.frombuffer(self.camera.texture.pixels, dtype=np.uint8).reshape((self.camera.texture.height, self.camera.texture.width, 4))

            try:
                # Convert RGBA pixels to BGR
                bgr_pixels = cv2.cvtColor(pixels, cv2.COLOR_RGBA2BGR)

                # Rotate the image
                rotated_pixels = np.rot90(bgr_pixels, k=3)

                # Capture frame from the camera
                buf1 = cv2.flip(rotated_pixels, 0)
                buf = buf1.tobytes()
                texture = Texture.create(size=(self.camera.resolution[1], self.camera.resolution[0]), colorfmt='bgr')
                texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
                self.image.texture = texture

                # Mirror the image horizontally
                mirrored_pixels = cv2.flip(rotated_pixels, 1)
                
                # Compress the frame using JPEG and then pickle the data
                ret, buffer = cv2.imencode(".jpg", mirrored_pixels, [int(cv2.IMWRITE_JPEG_QUALITY), 30])
                compressed_data = zlib.compress(pickle.dumps(buffer))
                nocomp_data = pickle.dumps(buffer)

                # Send the timestamp and compressed frame to the server
                self.sent_time = time.time()
                self.s.sendto(str(self.sent_time).encode(), (self.server_ip, self.server_port))
                self.s.sendto(compressed_data, (self.server_ip, self.server_port))

                # Calculate latency
                received_time = time.time()
                latency = received_time - self.sent_time
                self.latency_list.append(latency)
                print(f"Latency: {latency} seconds")

                # Calculate network usage for both compressed and uncompressed data
                total_nocomp_data = len(nocomp_data)
                self.nocomp_data_sent_list.append(total_nocomp_data)
                print(f"Total Data Sent: {total_nocomp_data} bytes")

                total_data_sent = len(compressed_data)
                self.data_sent_list.append(total_data_sent)
                print(f"Total Compressed Data Sent: {total_data_sent} bytes")

            except Exception as e:
                print(f"Error in update: {e}")

    ## Method to stop video streaming
    def stop_stream(self, instance):
        if self.server_ip:
            # Send stop signal to the server
            self.s.sendto(b'stop', (self.server_ip, self.server_port))
            print('Streaming stopped')
            self.streaming = False

            # Enable start button, disable stop button, and stop the camera
            self.start_button.disabled = False
            self.stop_button.disabled = True
            self.camera.play = False

            # Print the performance metrics
            avg_latency = sum(self.latency_list) / len(self.latency_list) if self.latency_list else 0
            avg_data_sent = sum(self.data_sent_list) / len(self.data_sent_list) if self.data_sent_list else 0
            avg_nocomp_data_sent = sum(self.nocomp_data_sent_list) / len(self.nocomp_data_sent_list) if self.nocomp_data_sent_list else 0

            print(f"Average Latency at client: {avg_latency} seconds")
            print(f"Average Sent Data at client: {avg_nocomp_data_sent} bytes")
            print(f"Average Compressed Sent Data at client: {avg_data_sent} bytes")

## Main function that calls the app to run
if __name__ == '__main__':
    VideoClientApp().run()
