# -*- coding: utf-8 -*-
from tcp_client import tcp
from enum import Enum
import sys
import os
import threading
import time

# Config constants
SERVER_IP = "192.168.1.152"
SERVER_PORT = "8888"
USER_PHOTO_PATH = "./ev_data/user_photo.png"
DRIVER_PHOTO_PATH = "./ev_data/driver_photo.png"
PRE_IMAGE_PATH = "./ev_data/inner_pre.png"
AFT_IMAGE_PATH = "./ev_data/inner_aft.png"
MESS_POINT_THRESHOLD = 0.9
RESEND_INTERVAL = 5

# Set state constants
STAT_ON = "on"
STAT_END = "end"
STAT_TERM = "terminate"

# Communication statements for send
COM_READY = "ready_for_rent"
COM_REQUIRE_USER_PHOTO = "require_user_photo"
COM_USER_PHOTO_SIZE_RECEIVED = "user_photo_size_received"
COM_USER_PHOTO_DATA_RECEIVED = "user_photo_data_received"
COM_DRIVING_START = "driving_start"
COM_DRIVING_END = "driving_end"
COM_RENT_END = "rent_end"
COM_REQUIRE_AFTERMATH = "require_aftermath"

# Communication statements for receive
COM_RENT_START = "start_rent"
COM_RESTORE_START = "restore_start"
COM_DRIVER_PHOTO_SIZE_RECEIVED = "driver_photo_size_received"
COM_DRIVER_PHOTO_DATA_RECEIVED = "driver_photo_data_received"
COM_MESS_POINT_RECEIVED = "mess_point_received"
COM_PRE_IMAGE_SIZE_RECEIVED = "pre_image_size_received"
COM_PRE_IMAGE_DATA_RECEIVED = "pre_image_data_received"
COM_AFT_IMAGE_SIZE_RECEIVED = "aft_image_size_received"
COM_AFT_IMAGE_DATA_RECEIVED = "aft_image_data_received"
COM_AFTERMATH_DONE = "aftermath_done"


class ProgState(Enum):
    IGN_OFF = 0
    IGN_ON = 1
    INIT = 2
    READY = 3
    RENT_START = 4
    USER_PHOTO_RECEIVED = 5
    EV_DRIVING_START = 6
    EV_DRIVING_END = 7
    WAIT_RESTORE = 8
    SEND_DRIVER_PHOTO = 9
    SEND_MESS_DATA = 10
    WAIT_AFTERMATH = 11
    UNKNOWN = -1


class EV(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        # Set initial program state
        self.state = ProgState.IGN_OFF
        # Variables
        self.tcp_socket = None

    def run(self):
        while True:
            if self.state == ProgState.IGN_ON:
                self.connect_server()
            elif self.state == ProgState.INIT:
                self.send_ready_statement()
            elif self.state == ProgState.READY:
                self.wait_for_rent_start()
            elif self.state == ProgState.RENT_START:
                self.receive_user_photo()
            elif self.state == ProgState.USER_PHOTO_RECEIVED:
                self.prepare_for_driving()
            elif self.state == ProgState.EV_DRIVING_START:
                self.runtime_dummy_function()
            elif self.state == ProgState.EV_DRIVING_END:
                self.reconnect_server()
            elif self.state == ProgState.WAIT_RESTORE:
                self.wait_for_restore_start()
            elif self.state == ProgState.SEND_DRIVER_PHOTO:
                self.send_illeagle_driver_photo()
            elif self.state == ProgState.SEND_MESS_DATA:
                self.send_mess_data()
            elif self.state == ProgState.WAIT_AFTERMATH:
                self.wait_for_aftermath_done()
            elif self.state == ProgState.UNKNOWN:
                self.terminate_sys()
            else:
                print("> Error: Inner state error.")
                self.terminate_sys()
                sys.exit(1)

    def set_state(self, operation):
        if str(operation) == STAT_ON and self.state == ProgState.IGN_OFF:
            print("> IGN ON.")
            self.state = ProgState.IGN_ON
        if str(operation) == STAT_END and self.state == ProgState.EV_DRIVING_START:
            print("> Driving end.")
            self.state = ProgState.EV_DRIVING_END
        if str(operation) == STAT_TERM:
            print("> Terminating system...")
            self.state = ProgState.UNKNOWN

    def connect_server(self):
        # Construct tcp connection
        self.tcp_socket = tcp(SERVER_IP, SERVER_PORT)
        print("> Server connected.")
        self.state = ProgState.INIT

    def send_ready_statement(self):
        self.tcp_socket.send_command(COM_READY)
        print("> EV ready for rent.")
        self.state = ProgState.READY

    def wait_for_rent_start(self):
        command = self.tcp_socket.receive_command()
        if command == COM_RENT_START:
            print("> EV rent started.")
            self.state = ProgState.RENT_START
        else:
            pass

    def receive_user_photo(self):
        # 1. Send user photo requirement
        self.tcp_socket.send_command(COM_REQUIRE_USER_PHOTO)
        print("> Waiting for user photo size.")
        str_photo_size = self.tcp_socket.receive_command()
        if str_photo_size.isdigit():
            photo_size = int(str_photo_size)
            if photo_size > 0:
                print("> Receiving user photo: %d Bytes" % photo_size)
                # 1. Send confirmed message (user photo size) to server
                self.tcp_socket.send(COM_USER_PHOTO_SIZE_RECEIVED)
                # 2. Receive file from server
                photo_data = self.tcp_socket.recv(photo_size)
                save_image(USER_PHOTO_PATH, photo_data)
                # 3. Send confirmed message (file received) to server
                self.tcp_socket.send(COM_USER_PHOTO_DATA_RECEIVED)
                print("> User photo saved.")
                self.state = ProgState.USER_PHOTO_RECEIVED
            else:
                print("> Error: user photo size invalid.")
                time.sleep(RESEND_INTERVAL)
        else:
            print("> Error: user photo size invalid.")
            time.sleep(RESEND_INTERVAL)

    def prepare_for_driving(self):
        # Take EV cabin photo before driving
        take_cabin_photo_pre()
        # 1. Inform server that EV will leave
        self.tcp_socket.send_command(COM_DRIVING_START)
        # 2. Release connection
        self.tcp_socket.close()
        self.tcp_socket = None
        print("> EV driving started.")
        self.state = ProgState.EV_DRIVING_START

    def runtime_dummy_function(self):
        # In this function the driver identify process will be executed
        driver_identify()
        if self.state == ProgState.EV_DRIVING_START:
            time.sleep(3)

    def reconnect_server(self):
        # Construct tcp connection
        self.tcp_socket = tcp(SERVER_IP, SERVER_PORT)
        print("> Server connected.")
        self.tcp_socket.send_command(COM_DRIVING_END)
        print("> EV driving end, waiting for restore command.")
        self.state = ProgState.WAIT_RESTORE

    def wait_for_restore_start(self):
        # Wait for restore command from server
        command = self.tcp_socket.receive_command()
        if command == COM_RESTORE_START:
            print("> EV restore start, prepare to send data.")
            self.state = ProgState.SEND_DRIVER_PHOTO
        else:
            pass

    def send_illeagle_driver_photo(self):
        photo_size, photo_data = load_image(DRIVER_PHOTO_PATH)
        # Send photo size
        self.tcp_socket.send_command(photo_size)
        # Wait server reply
        reply = self.tcp_socket.receive_command()
        if reply == COM_DRIVER_PHOTO_SIZE_RECEIVED:
            if photo_size > 0:
                # Send driver photo data
                self.tcp_socket.send_file(photo_data)
                # Wait server reply
                reply = self.tcp_socket.receive_command()
                if reply == COM_DRIVER_PHOTO_DATA_RECEIVED:
                    self.state = ProgState.SEND_MESS_DATA
                    print("> Illeagle driver photo sent.")
                else:
                    time.sleep(RESEND_INTERVAL)
                    print("> Warning: resend illeagle driver photo.")
            else:
                self.state = ProgState.SEND_MESS_DATA
                print("> No need to send illeagle driver photo.")
        else:
            time.sleep(RESEND_INTERVAL)
            print("> Warning: resend illeagle driver photo.")

    def send_mess_data(self):
        # 1. Send mess point
        mess_point = 0.8
        self.tcp_socket.send_command(mess_point)
        # Wait server reply
        reply = self.tcp_socket.receive_command()
        if reply == COM_MESS_POINT_RECEIVED:
            # If mess point < 0.9, then need aftermath treatment
            if mess_point < MESS_POINT_THRESHOLD:
                # 2. Send pre-img size
                img_size, img_data = load_image(PRE_IMAGE_PATH)
                self.tcp_socket.send_command(img_size)
                # Wait server reply
                reply = self.tcp_socket.receive_command()
                if reply == COM_PRE_IMAGE_SIZE_RECEIVED:
                    # 3. Send pre-img data
                    self.tcp_socket.send_file(img_data)
                    # Wait server reply
                    reply = self.tcp_socket.receive_command()
                    if reply == COM_PRE_IMAGE_DATA_RECEIVED:
                        # 4. Send aft-img size
                        img_size, img_data = load_image(AFT_IMAGE_PATH)
                        self.tcp_socket.send_command(img_size)
                        # Wait server reply
                        reply = self.tcp_socket.receive_command()
                        if reply == COM_AFT_IMAGE_SIZE_RECEIVED:
                            # 5. Send aft-img data
                            self.tcp_socket.send_file(img_data)
                            # Wait server reply
                            reply = self.tcp_socket.receive_command()
                            if reply == COM_AFT_IMAGE_DATA_RECEIVED:
                                self.tcp_socket.send_command(COM_REQUIRE_AFTERMATH)
                                self.state = ProgState.WAIT_AFTERMATH
                                print("> Need aftermath treatment.")
                            else:
                                time.sleep(RESEND_INTERVAL)
                                print("> Warning: resend mess data.")
                        else:
                            time.sleep(RESEND_INTERVAL)
                            print("> Warning: resend mess data.")
                    else:
                        time.sleep(RESEND_INTERVAL)
                        print("> Warning: resend mess data.")
                else:
                    time.sleep(RESEND_INTERVAL)
                    print("> Warning: resend mess data.")
            else:
                self.tcp_socket.send_command(COM_RENT_END)
                self.tcp_socket.close()
                self.tcp_socket = None
                self.state = ProgState.IGN_OFF
                print("> No aftermath treatment is required, entire rent closed.")
        else:
            time.sleep(RESEND_INTERVAL)
            print("> Warning: resend mess data.")

    def wait_for_aftermath_done(self):
        # Wait for restore command from server
        command = self.tcp_socket.receive_command()
        if command == COM_AFTERMATH_DONE:
            print("> Aftermath done, rechecking...")
            # 1. Send mess point
            mess_point = 0.95
            self.tcp_socket.send_command(mess_point)
            # Wait server reply
            reply = self.tcp_socket.receive_command()
            if reply == COM_MESS_POINT_RECEIVED:
                # If mess point < 0.9, then need aftermath treatment
                if mess_point < MESS_POINT_THRESHOLD:
                    # 2. Send pre-img size
                    img_size, img_data = load_image(PRE_IMAGE_PATH)
                    self.tcp_socket.send_command(img_size)
                    # Wait server reply
                    reply = self.tcp_socket.receive_command()
                    if reply == COM_PRE_IMAGE_SIZE_RECEIVED:
                        # 3. Send pre-img data
                        self.tcp_socket.send_file(img_data)
                        # Wait server reply
                        reply = self.tcp_socket.receive_command()
                        if reply == COM_PRE_IMAGE_DATA_RECEIVED:
                            # 4. Send aft-img size
                            img_size, img_data = load_image(AFT_IMAGE_PATH)
                            self.tcp_socket.send_command(img_size)
                            # Wait server reply
                            reply = self.tcp_socket.receive_command()
                            if reply == COM_AFT_IMAGE_SIZE_RECEIVED:
                                # 5. Send aft-img data
                                self.tcp_socket.send_file(img_data)
                                # Wait server reply
                                reply = self.tcp_socket.receive_command()
                                if reply == COM_AFT_IMAGE_DATA_RECEIVED:
                                    self.tcp_socket.send_command(COM_REQUIRE_AFTERMATH)
                                    self.state = ProgState.WAIT_AFTERMATH
                                    print("> Need aftermath treatment.")
                                else:
                                    time.sleep(RESEND_INTERVAL)
                                    print("> Warning: resend mess data.")
                            else:
                                time.sleep(RESEND_INTERVAL)
                                print("> Warning: resend mess data.")
                        else:
                            time.sleep(RESEND_INTERVAL)
                            print("> Warning: resend mess data.")
                    else:
                        time.sleep(RESEND_INTERVAL)
                        print("> Warning: resend mess data.")
                else:
                    self.tcp_socket.send_command(COM_RENT_END)
                    self.tcp_socket.close()
                    self.tcp_socket = None
                    self.state = ProgState.IGN_OFF
                    print("> Aftermath treatment is done, entire rent closed.")
            else:
                time.sleep(RESEND_INTERVAL)
                print("> Warning: resend mess data.")
        else:
            pass

    def terminate_sys(self):
        if self.tcp_socket:
            self.tcp_socket.close()
            self.tcp_socket = None
        print("> System terminated.")


def take_cabin_photo_pre():
    pass


def take_cabin_photo_aft():
    pass


def driver_identify():
    pass


def save_image(path, data):
    try:
        with open(path, "wb") as f:
            f.write(data)
    except IOError:
        print("Cannot save image.")
        sys.exit(1)


def load_image(path):
    img_size = 0
    img_data = None
    if os.path.isfile(path):
        try:
            with open(path, "rb") as f:
                img_data = f.read()
                img_size = len(img_data)
        except IOError:
            print("Cannot load image.")
            sys.exit(1)
    return img_size, img_data


if __name__ == '__main__':
    # Construct new thread
    ev = EV()
    # Start thread
    ev.start()
    while True:
        cmd = input('>: ')
        ev.set_state(cmd)
