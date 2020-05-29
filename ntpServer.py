import struct
import socket


IP = ''
PORT = 123
BUFFER = 48
WAITING_TIME = 5
OTHER_SERVER = ''
UP = 0
FORMAT = "!32s 4I"


def start():
    print('up time ', UP)
    print('time server ', OTHER_SERVER)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind((IP, PORT))
        print('bind')
        server.settimeout(0.1)
        while True:
            try:
                recv, address = server.recvfrom(BUFFER)
                print('accepted ', address)
                recv = get_time_from_server(OTHER_SERVER, recv)
                if not recv: continue
                recv = conversion(recv)
                server.sendto(recv, address)
                print('sent ', address)
            except socket.timeout:
                pass


def get_fraction(number, precision):
    return int((number - int(number)) * 2 ** precision)


def conversion(data):
    unpacked_data = struct.unpack(FORMAT, data)
    receive = unpacked_data[1] + unpacked_data[2] / 2 ** 32 + UP
    transmit = unpacked_data[3] + unpacked_data[4] / 2 ** 32 + UP
    data = struct.pack(FORMAT,
                       unpacked_data[0],
                       int(receive),
                       get_fraction(receive, 32),
                       int(transmit),
                       get_fraction(transmit, 32))
    return data


def get_time_from_server(server, data):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.settimeout(WAITING_TIME)
            client.sendto(data, (server, PORT))
            data = client.recv(48)
            return data
    except socket.timeout:
        pass


def parse_config(path):
    with open(path, encoding='utf-8') as file:
        for line in file.readlines():
            command = line.split(' ')
            command[-1] = command[-1][0:-1]
            if len(command) == 2: two_command(command)


def two_command(command):
    global UP
    global OTHER_SERVER
    if command[0] == 'uptime':
        UP = int(command[1])
    elif command[0] == 'ntpserver':
        OTHER_SERVER = command[1]
    else:
        raise Exception('Unknown command: ' + command[0])


def main():
    parse_config('config.cnf')
    try:
        start()
    except KeyboardInterrupt:
        pass
    print('stop')


if __name__ == '__main__':
    main()
