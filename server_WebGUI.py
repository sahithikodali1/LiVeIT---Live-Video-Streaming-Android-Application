#import libraries/packages required
import socket
import numpy as np
import os
import cv2
import pickle

#create a UDP socket
s =  socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set the IP address and port for the server
ip = "10.0.0.155"
port = 6666

# Bind the socket to the specified IP and port
s.bind((ip,port))

# Print server information
print(f"Server listening on {ip}:{port}")
print("Waiting for video stream from client...")

# Flag to stop the server
stop_server = False

# Counter to indicate the start of video streaming
counter = 0

# Main loop to receive and process data from the client
while not stop_server:

    # Receive data from the client
    x = s.recvfrom(1000000)
    clientip = x[1][0]
    data = x[0]
    
    # Check if the received data is a stop signal or empty
    if data == b'stop' or not data:
        print(f"Connection closed from client")
        stop_server = True
        break

    # If it's the first iteration, print a message indicating video streaming has started
    if counter == 0:
        counter += 1
        print("Video streaming started")

    # Unpickle the data and display the image
    data = pickle.loads(data)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    cv2.imshow('Video Server', img)

    # Check for the 'Esc' key to stop the server
    key =  cv2.waitKey(1) & 0xFF 
    if key == 27:
        print(f"Connection closed from client {clientip}")
        stop_server=True
        break

# Print a message indicating the end of video streaming
print("Video streaming ended")

# Close the OpenCV windows and socket
cv2.destroyAllWindows()
s.close()