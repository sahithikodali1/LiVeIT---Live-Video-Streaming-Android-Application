#import libraries/packages required
import socket
import numpy as np
import os
import cv2
import pickle
import time
import zlib

#create a UDP socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set the IP address and port for the server
ip = "10.0.0.155"
port = 6666

# Bind the socket to the specified IP and port
s.bind((ip, port))

# Print server information
print(f"Server listening on {ip}:{port}")
print("Waiting for video stream from client...")

# Flag to stop the server
stop_server = False

# Variables to track performance metrics
total_data_received = 0
total_network_usage = 0

#start tracking time
start_time = time.time()

# Lists to store latency, received data, and network usage for later analysis
latency_list = []
received_data_list = []
network_usage_list = []

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

    try:
        # Attempt to decode the received data as a timestamp (for measuring latency)
        sent_time_from_client = float(data.decode())
        received_time = time.time()
        latency = received_time - sent_time_from_client
        latency_list.append(latency)
        print(f"Latency: {latency} seconds")

    except ValueError:
        # If decoding as timestamp fails, treat it as image data
        total_data_received += len(data)
        received_data_list.append(len(data))
        print(f"Total Data Received: {total_data_received} bytes")

        # Decompress the compressed data
        decompressed_data = zlib.decompress(data)

        # Unpickle the data and display the image
        img_data = pickle.loads(decompressed_data)
        img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
        cv2.imshow('Video Server', img)

    # Check for the 'Esc' key to stop the server
    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        print(f"Connection closed from client {clientip}")
        stop_server = True
        break

# Print the performance metrics
avg_latency = sum(latency_list) / len(latency_list) if latency_list else 0
avg_received_data = sum(received_data_list) / len(received_data_list) if received_data_list else 0

print(f"Average Latency at server: {avg_latency} seconds")
print(f"Average Received Data at server: {avg_received_data} bytes")

# Print a message indicating the end of video streaming
print("Video streaming ended")

# Close the OpenCV windows and socket
cv2.destroyAllWindows()
s.close()
