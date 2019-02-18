# -*- coding: utf-8 -*-

import socket
import sys
import time


def main():
    # Construct socket object
    try:
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as e:
        print("Error creating socket: %s" % e)
        sys.exit(1)
    # Bind to localhost
    tcp_socket.bind(("", 8888))
    # Set to passive mode, set the max connection
    tcp_socket.listen(4)

    # Send data to server
    while True:
        print('Wait for connection ...')
        client_socket, client_addr = tcp_socket.accept()
        print("Connection from: ", client_addr)
        while True:
            try:
                data = client_socket.recv(32).decode()
            except socket.error as e:
                print("Error receiving data: %s" % e)
                sys.exit(1)
            if not data:
                print("Connection released.")
                break
            recv_cmd = str(data)
            if recv_cmd == "img":
                send_file("1.jpg", client_socket)
            else:
                print(str(data))
            # Sleep 1s for data sending
            time.sleep(1)
        # Close client socket
        client_socket.close()

    # Close socket
    # tcp_socket.close()


def send_file(file_path, client_socket):
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
            file_size = len(file_data)
            # 1. Send file size to client
            client_socket.send(str(file_size).encode())
            print("Sending file, %d Bytes" % file_size)
            # 2. Get confirmed message (file size) from client
            str_data = client_socket.recv(32).decode()
            if int(str_data) == file_size:
                # 3. Send file to client
                client_socket.send(file_data)
                # 4. Get confirmed message (file received) from client
                str_data = client_socket.recv(32).decode()
                if str_data == "received":
                    print("File send succeed.")
                else:
                    print("File send failed.")

    except IOError:
        print("Cannot open file.")
        sys.exit(1)


if __name__ == '__main__':
    main()
