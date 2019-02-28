# -*- coding: utf-8 -*-
import socket
import sys
import time

# Config constants
MAX_CMD_SIZE = 64
WAIT_TIME_CMD_SEND = 1
WAIT_TIME_FILE_SEND = 5


class tcp:

    def __init__(self, ip, port):
        # Construct socket object
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as e:
            print("Error creating socket: %s" % e)
            sys.exit(1)
        # Connect server
        if isinstance(port, str):
            _port = int(port)
        else:
            _port = port
        try:
            self.tcp_socket.connect((ip, _port))
            print("Network connected.")
        except socket.gaierror as e:
            print("Address-related error connecting to server: %s" % e)
            sys.exit(1)
        except socket.error as e:
            print("Connection error: %s" % e)
            sys.exit(1)

    def receive_command(self):
        str_data = self.tcp_socket.recv(MAX_CMD_SIZE).decode()
        return str_data

    def receive_file(self, file_size):
        if isinstance(file_size, int):
            size = file_size
        else:
            size = int(file_size)
        binary_data = self.tcp_socket.recv(size)
        return binary_data

    def send_command(self, command):
        if command is not None:
            if isinstance(command, str):
                cmd = command
            else:
                cmd = str(command)
            try:
                self.tcp_socket.send(cmd.encode())
            except socket.error as e:
                print("Error sending command: ", cmd)
                print("Error: %s" % e)
                sys.exit(1)
            # Sleep 1s for command sending
            time.sleep(WAIT_TIME_CMD_SEND)
        else:
            print("Warning: Sending empty command.")

    def send_file(self, file):
        if file:
            try:
                self.tcp_socket.send(file)
            except socket.error as e:
                print("Error sending file: %s" % e)
                sys.exit(1)
            # Sleep 5s for command sending
            time.sleep(WAIT_TIME_FILE_SEND)
        else:
            print("Warning: Sending empty file.")

    def close(self):
        self.tcp_socket.close()
