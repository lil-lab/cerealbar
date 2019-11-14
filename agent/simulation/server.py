"""Implements a server that controls connection to a Unity standalone application."""
import json
import socket
import sys
from subprocess import Popen
from threading import Thread
from time import sleep
from typing import Tuple

from agent.environment import state_delta
from agent.simulation import util


class ServerSocket:
    """ Stores the sockets connecting to the Unity game."""

    def __init__(self, ip_address: str, port: int):
        self._ip_address: str = ip_address
        self._port: int = port

        self._server_socket: socket.SocketKind = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self._ip_address, self._port))
        self._server_socket.listen(5)

        print('Listening at ' + str(self._ip_address) + ':' + str(self._port))
        self.client_socket: socket.SocketKind = None

        self._current_process: Popen = None

    def _accept_connection(self) -> None:
        try:
            client: Tuple[socket.SocketKind, Tuple[str, int]] = self._server_socket.accept()
            self.client_socket: socket.SocketKind = client[0]
            self.client_socket.settimeout(10)
        except Exception as error:
            print('Connection error: ', error)
            self._server_socket.close()
            sys.exit()

    def receive_data(self) -> bytes:
        """Receives data from the standalone application and forwards it to the caller."""
        data: bytes = b''
        try:
            message_length: int = int.from_bytes(self.client_socket.recv(4), byteorder='little')

            while len(data) < message_length:
                chunk: bytes = self.client_socket.recv(min(message_length - len(data), 2048))
                if chunk == b'':
                    raise RuntimeError('Socket connection broken.')
                data += chunk
        except socket.timeout as error:
            print('Timeout exception: ')
            print(error)
            return b''

        return data

    def start_unity(self) -> Tuple[Thread, Popen]:
        """Starts the Unity standalone."""
        thread: Thread = Thread(target=self._accept_connection)
        thread.start()
        sleep(1)

        process: Popen = util.start_standalone()

        self._current_process = process

        thread.join()
        return thread, process

    def start_new_game(self, seed: int, num_cards: int) -> None:
        """Starts a new game given a seed and the number of cards (which can deterministically set the
        props/terrain).
        """
        msg_suffix: str = ', ' + str(seed) + ',' + str(num_cards)
        thread: Thread = Thread(target=self._accept_connection)
        thread.start()
        sleep(1)
        self.client_socket.send(('restart' + msg_suffix).encode())

        thread.join()
        self.client_socket.send(('start' + msg_suffix).encode())

    def set_game_state(self, state: state_delta.StateDelta) -> None:
        """Sets the state of the board, including card and player locations and properties."""
        self.client_socket.send(('state,' + json.dumps(state.to_dict())).encode())
        self.receive_data()

    def send_data(self, data: str) -> None:
        """Sends data to the Unity standalone."""
        self.client_socket.send(data.encode())

    def close(self):
        """Quits the standalone application."""
        self._server_socket.close()
        self.client_socket.close()
        util.quit_standalone(self._current_process)
