import json
import socket
import struct
import time
from dataclasses import dataclass


@dataclass
class MCBEInfo:
    host: str
    port: int
    motd: str
    protocol_version: int
    server_version: str
    current_players_count: int
    max_players_count: int
    unique_id: str
    world_name: str
    game_mode: str
    port_ipv4: int
    port_ipv6: int
    delay: int


@dataclass
class MCjEInfo:
    host: str
    port: int
    description: str
    protocol_version: int
    server_version: str
    current_players_count: int
    max_players_count: int
    delay: int


def get_mcbe(host: str, port: int = 19132) -> MCBEInfo:
    addr = (host, port)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(5)
    data = b'\x01\x00\x00\x00\x00\x24\x0D\x12\xD3\x00\xFF\xFF\x00\xFE\xFE\xFE\xFE\xFD\xFD\xFD\xFD\x12\x34\x56\x78'
    s.sendto(data, addr)
    start_time = time.time()
    recv_data = s.recv(1024)
    delay = int((time.time() - start_time) * 1000)
    s.close()
    recv_data = recv_data.decode('utf-8', errors='ignore').split(';')
    return MCBEInfo(
        host=host,
        port=port,
        motd=recv_data[1],
        protocol_version=int(recv_data[2]),
        server_version=recv_data[3],
        current_players_count=int(recv_data[4]),
        max_players_count=int(recv_data[5]),
        unique_id=recv_data[6],
        world_name=recv_data[7],
        game_mode=recv_data[8],
        port_ipv4=int(recv_data[10]),
        port_ipv6=int(recv_data[11]),
        delay=delay
    )


def _pack_varint(data):
    """ Pack the var int """
    ordinal = b''

    while True:
        byte = data & 0x7F
        data >>= 7
        ordinal += struct.pack('B', byte | (0x80 if data > 0 else 0))

        if data == 0:
            break

    return ordinal


def _send_data(connection, *args):
    """ Send the data on the connection """

    def _pack_data(data):
        """ Page the data """
        if type(data) is str:
            data = data.encode('utf8')
            return _pack_varint(len(data)) + data
        elif type(data) is int:
            return struct.pack('H', data)
        elif type(data) is float:
            return struct.pack('Q', int(data))
        else:
            return data

    data = b''

    for arg in args:
        data += _pack_data(arg)

    connection.send(_pack_varint(len(data)) + data)


def _read_fully(connection, extra_varint=False):
    """ Read the connection and return the bytes """

    def _unpack_varint(sock):
        """ Unpack the varint """
        data = 0
        for i in range(5):
            ordinal = sock.recv(1)

            if len(ordinal) == 0:
                break

            byte = ord(ordinal)
            data |= (byte & 0x7F) << 7 * i

            if not byte & 0x80:
                break

        return data

    packet_length = _unpack_varint(connection)
    packet_id = _unpack_varint(connection)
    byte = b''

    if extra_varint:
        # Packet contained netty header offset for this
        if packet_id > packet_length:
            _unpack_varint(connection)

        extra_length = _unpack_varint(connection)

        while len(byte) < extra_length:
            byte += connection.recv(extra_length)

    else:
        byte = connection.recv(packet_length)

    return byte


def get_mcje(host, port=25565, timeout=5) -> MCjEInfo:
    """ Get the status response """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.settimeout(timeout)
        connection.connect((host, port))

        # Send handshake + status request
        _send_data(connection, b'\x00\x00', host, port, b'\x01')
        _send_data(connection, b'\x00')

        # Read response, offset for string length
        data = _read_fully(connection, extra_varint=True)

        # Send and read unix time
        _send_data(connection, b'\x01', time.time() * 1000)
        unix = _read_fully(connection)

    # Load json and return
    response = json.loads(data.decode('utf-8', errors='ignore'))
    response['ping'] = int(time.time() * 1000) - struct.unpack('Q', unix)[0]

    return MCjEInfo(
        host=host,
        port=port,
        description=response['description']['text'],
        delay=response['ping'],
        protocol_version=response['version']['protocol'],
        server_version=response['version']['name'],
        current_players_count=response['players']['online'],
        max_players_count=response['players']['max']
    )


if __name__ == '__main__':
    print(get_mcje('aoyin.games'))
    print(get_mcje('cow.mcla.fun', 11205))
    print(get_mcje('root.yingluo.world', 58001))
