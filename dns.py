import socket
import pickle
import time
try:
    from dnslib import *
except ModuleNotFoundError:
    raise Exception('Не удалось импортировать модуль dnslib, пожалуйста установите модуль через команду pip install dnslib')


IP = ''
DNS = '8.8.8.8'
PORT = 53
DICT = {}
WAITING_TIME = 5


def start():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind((IP, PORT))
        server.settimeout(0.1)
        while True:
            try:
                data = []
                recv, address = server.recvfrom(1024)
                if not recv: continue

                update_dict()
                
                server.sendto(response(recv), address)

            except socket.timeout:
                pass


def response(recv):
    request = DNSRecord.parse(recv)

    qname = request.q.qname
    qn = str(qname)
    qtype = request.q.qtype

    if (qn, qtype) not in DICT:
        recv = send_request(DNS, recv)
        request = DNSRecord.parse(recv)

        save_to_dict(request.rr, qtype)
        save_to_dict(request.auth, qtype)
        save_to_dict(request.ar, qtype)

    if (qn, qtype) not in DICT: return None

    package = DNSRecord(DNSHeader(id=request.header.id), q=request.q)

    info = DICT[(qn, qtype)]
    package.add_answer(RR(rname=qname, rtype=info[0], rclass=1, ttl=int(info[1] - time.time()), rdata=info[2]))

    return package.pack()


def save_to_dict(a_array, qtype):
    for a in a_array:
        DICT[(str(a.rname), qtype)] = (a.rtype, time.time() + a.ttl, a.rdata)


def save(data, path):
    with open(path, "wb") as file:
        pickle.dump(data, file)


def load(path):
    try:
        with open(path, "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return {}


def update_dict():
    for key in DICT.keys():
        if DICT[key][1] <= time.time():
            DICT.pop(key)


def send_request(server, data):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.settimeout(WAITING_TIME)
            client.sendto(data, (server, PORT))
            data = client.recv(1024)
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
    global DNS
    if command[0] == 'dns':
        DNS = command[1]
    else:
        raise Exception('Unknown command: ' + command[0])


def main():
    parse_config('config.cnf')
    global DICT
    try:
        DICT = load('data.pickle')
        start()
    finally:
        save(DICT, 'data.pickle')


if __name__ == '__main__':
    main()
