# !/usr/bin/python
# -*-coding:utf-8-*-
# bugreport:lyq19961011@gmail.com
import sys
import socket
import struct
import time
import hashlib
import json


def send_json_data(host, packet, port):
    sock_udp.sendto(packet, (host, port))


def check_md5(md5, md5_recv):
    for i in range(16):
        if md5[i] != md5_recv[i]:
            print ('MD5 check error!')
            return False
    return True


def login(host, packet, message_display):
    send_json_data(host, packet, 3848)
    try:
        response = sock_udp.recv(4096)
        response = [i for i in struct.unpack('B' * len(response), response)]
        response = decrypt(response)
        md5_recv = response[2:18]
        response[2:18] = [i * 0 for i in range(16)]
        md5 = hashlib.md5(b''.join([struct.pack('B', i)
                                    for i in response])).digest()
        md5 = struct.unpack('16B', md5)
        if check_md5(md5, md5_recv) is False:
            return False
    except socket.error:
        return False
    login_status = response[20]
    session_len = response[22]
    session = response[23:session_len + 23]
    response[23:session_len + 23] = [i * 0 for i in range(session_len)]
    if message_display == '1':
        try:
            message_len = response[response.index(11) + 1]
            message = response[response.index(
                11) + 2:message_len + response.index(11) + 2]
            message = b''.join([struct.pack('B', i)
                                for i in message]).decode('gbk')
        except Exception, e:
            print (e)
            print ('Recvice message for server failed.')
            message = ''
    if login_status == 0:
        if message_display == '1':
            print (message)
            return False
        else:
            return False
    elif message_display == '1':
        print (message)
        print ('Ctrl + C to Exit or Login out!')
        return session
    else:
        print ('Login in success')
        print ('Ctrl + C to Exit or Login out!')
        return session


def breathe(host, mac_address, ip_addr, session, index, block):
    time.sleep(1)
    while True:
        breathe_packet = generate_breathe(
            mac_address, ip_addr, session, index, block)
        send_json_data(host, breathe_packet, 3848)
        try:
            breathe_status = sock_udp.recv(4096)
            breathe_status = [i for i in struct.unpack(
                'B' * len(breathe_status), breathe_status)]
            breathe_status = decrypt(breathe_status)
            md5_recv = breathe_status[2:18]
            breathe_status[2:18] = [i * 0 for i in range(16)]
            md5 = hashlib.md5(b''.join([struct.pack('B', i)
                                        for i in breathe_status])).digest()
            md5 = struct.unpack('16B', md5)
            if check_md5(md5, md5_recv) is False:
                return False
        except socket.error:
            return False
        if breathe_status[20] == 0:
            return False
        index += 3
        try:
            time.sleep(20)
        except KeyboardInterrupt:
            downnet_packet = generate_downnet(
                mac_address, ip_addr, session, index, block)
            send_json_data(host, downnet_packet, 3848)
            print ('Downnet success.')
            sock_udp.close()
            sys.exit()


def encrypt(packet):
    return_packet = []
    for i in packet:
        i = (i & 0x80) >> 6 | (i & 0x40) >> 4 | (i & 0x20) >> 2 | (i & 0x10) << 2 | (
            i & 0x08) << 2 | (i & 0x04) << 2 | (i & 0x02) >> 1 | (i & 0x01) << 7
        return_packet.append(i)
    return return_packet


def decrypt(packet):
    return_packet = []
    for i in packet:
        i = (i & 0x80) >> 7 | (i & 0x40) >> 2 | (i & 0x20) >> 2 | (i & 0x10) >> 2 | (
            i & 0x08) << 2 | (i & 0x04) << 4 | (i & 0x02) << 6 | (i & 0x01) << 1
        return_packet.append(i)
    return return_packet


def generate_upnet(mac, user, pwd, ip, dhcp, service, version):
    packet = []
    packet.append(0x01)
    packet_len = 38 + len(user) + len(pwd) + len(ip) + \
        len(service) + len(dhcp) + len(version)
    packet.append(packet_len)
    packet.extend([i * 0x00 for i in range(16)])
    packet.extend([0x07, 0x08])
    packet.extend([int(i, 16) for i in mac.split(':')])
    packet.extend([0x01, len(user) + 2])
    packet.extend([ord(i) for i in user])
    packet.extend([0x02, len(pwd) + 2])
    packet.extend([ord(i) for i in pwd])
    packet.extend([0x09, len(ip) + 2])
    packet.extend([ord(i) for i in ip])
    packet.extend([0x0a, len(service) + 2])
    packet.extend([ord(i) for i in service])
    packet.extend([0x0e, len(dhcp) + 2])
    packet.extend([int(i) for i in dhcp])
    packet.extend([0x1f, len(version) + 2])
    packet.extend([ord(i) for i in version])
    md5 = hashlib.md5(b''.join([struct.pack('B', i) for i in packet])).digest()
    packet[2:18] = struct.unpack('16B', md5)
    packet = encrypt(packet)
    packet = b''.join([struct.pack('B', i) for i in packet])
    return packet


def generate_breathe(mac, ip, session, index, block):
    index = hex(index)[2:]
    packet = []
    packet.append(0x03)
    packet_len = len(session) + 88
    packet.append(packet_len)
    packet.extend([i * 0 for i in range(16)])
    packet.extend([0x08, len(session) + 2])
    packet.extend(session)
    packet.extend([0x09, 0x12])
    packet.extend([ord(i) for i in ip])
    packet.extend([i * 0 for i in range(16 - len(ip))])
    packet.extend([0x07, 0x08])
    packet.extend([int(i, 16) for i in mac.split(':')])
    packet.extend([0x14, 0x06])
    packet.extend([int(index[0:-6], 16), int(index[-6:-4], 16),
                   int(index[-4:-2], 16), int(index[-2:], 16)])
    packet.extend(i for i in block)
    md5 = hashlib.md5(b''.join([struct.pack('B', i) for i in packet])).digest()
    packet[2:18] = struct.unpack('16B', md5)
    packet = encrypt(packet)
    packet = b''.join([struct.pack('B', i) for i in packet])
    return packet


def generate_downnet(mac, ip, session, index, block):
    index = hex(index)[2:]
    packet = []
    packet.append(0x05)
    packet_len = len(session) + 88
    packet.append(packet_len)
    packet.extend([i * 0 for i in range(16)])
    packet.extend([0x08, len(session) + 2])
    packet.extend(session)
    packet.extend([0x09, 0x12])
    packet.extend([ord(i) for i in ip])
    packet.extend([i * 0 for i in range(16 - len(ip))])
    packet.extend([0x07, 0x08])
    packet.extend([int(i, 16) for i in mac.split(':')])
    packet.extend([0x14, 0x06])
    packet.extend([int(index[0:-6], 16), int(index[-6:-4], 16),
                   int(index[-4:-2], 16), int(index[-2:], 16)])
    packet.extend(i for i in block)
    md5 = hashlib.md5(b''.join([struct.pack('B', i) for i in packet])).digest()
    packet[2:18] = struct.unpack('16B', md5)
    packet = encrypt(packet)
    packet = b''.join([struct.pack('B', i) for i in packet])
    return packet


def search_service(mac, host_ip):
    packet = []
    packet.append(0x07)
    packet_len = 1 + 1 + 16 + 1 + 1 + 5 + 1 + 1 + 6
    packet.append(packet_len)
    packet.extend([i * 0 for i in range(16)])
    packet.append(0x08)
    packet.append(0x07)
    packet.extend([i * 1 for i in range(5)])
    packet.append(0x07)
    packet.append(0x08)
    packet.extend([int(i, 16) for i in mac.split(':')])
    md5 = hashlib.md5(b''.join([struct.pack('B', i) for i in packet])).digest()
    packet[2:18] = struct.unpack('16B', md5)
    packet = encrypt(packet)
    packet = b''.join([struct.pack('B', i) for i in packet])
    send_json_data(host_ip, packet, 3848)
    try:
        packet_recv = sock_udp.recv(4096)
    except socket.error:
        print('Search service failed.Reason:server no response!')
        sys.exit(1)
    packet_recv = [i for i in struct.unpack(
        'B' * len(packet_recv), packet_recv)]
    packet_recv = decrypt(packet_recv)
    md5_recv = packet_recv[2:18]
    packet_recv[2:18] = [i * 0 for i in range(16)]
    md5 = hashlib.md5(b''.join([struct.pack('B', i)
                                for i in packet_recv])).digest()

    md5 = struct.unpack('16B', md5)
    if check_md5(md5, md5_recv) is True:
        service_index = packet_recv.index(10)
        service_len = packet_recv[service_index + 1] - 2
        service = packet_recv[service_index +
                              2:service_index + 2 + service_len]
        print ('Search service success:')
        stra = ''
        for i in service:
            stra += chr(i)
        print (stra)
        return (stra)
    else:
        sys.exit(1)


def search_server_ip(ip, mac):
    packet = []
    packet.append(0x0c)
    packet_len = 1 + 1 + 16 + 1 + 1 + 5 + 1 + 1 + 16 + 1 + 1 + 6
    packet.append(packet_len)
    packet.extend([i * 0 for i in range(16)])
    packet.append(0x08)
    packet.append(0x07)
    packet.extend([i * 1 for i in range(5)])
    packet.append(0x09)
    packet.append(0x12)
    packet.extend([ord(i) for i in ip])
    packet.extend([i * 0 for i in range(16 - len(ip))])
    packet.append(0x07)
    packet.append(0x08)
    packet.extend([int(i, 16) for i in mac.split(':')])
    md5 = hashlib.md5(b''.join([struct.pack('B', i) for i in packet])).digest()
    packet[2:18] = struct.unpack('16B', md5)
    packet = encrypt(packet)
    packet = b''.join([struct.pack('B', i) for i in packet])
    send_json_data('1.1.1.8', packet, 3850)
    try:
        packet_recv = sock_udp.recv(4096)
    except socket.error:
        print('Search server ip failed.Reason:server no response!')
        sys.exit(1)
    packet_recv = [i for i in struct.unpack(
        'B' * len(packet_recv), packet_recv)]
    packet_recv = decrypt(packet_recv)
    md5_recv = packet_recv[2:18]
    packet_recv[2:18] = [i * 0 for i in range(16)]
    md5 = hashlib.md5(b''.join([struct.pack('B', i)
                                for i in packet_recv])).digest()

    md5 = struct.unpack('16B', md5)
    if check_md5(md5, md5_recv) is True:
        server_index = packet_recv.index(0x0c)
        server = packet_recv[server_index + 2:server_index + 6]
        print ('Search host ip success:')
        stra = ''
        for i in server:
            stra += str(i) + '.'
        print (stra[:-1])
        return stra[:-1]
    else:
        sys.exit(1)


def decode():
    reload(sys)
    sys.setdefaultencoding('utf-8')


def delay():
    time.sleep(10)


def main():
    if delay_enable == '1':
        delay()
    index = 0x01000000
    block = [0x2a, 0x06, 0, 0, 0, 0, 0x2b, 0x06, 0, 0, 0, 0, 0x2c, 0x06, 0, 0, 0,
             0, 0x2d, 0x06, 0, 0, 0, 0, 0x2e, 0x06, 0, 0, 0, 0, 0x2f, 0x06, 0, 0, 0, 0]
    while True:
        upnet_packet = generate_upnet(
            auth_mac_address, username, password, auth_ip, dhcp_setting, service_type, client_version)
        session = login(auth_host_ip, upnet_packet, message_display_enable)
        if session is False:
            if reconnet_enable == '1':
                print ('Login failed..Relogining...')
                time.sleep(10)
                main()
            else:
                print ('Lgoin failed...')
                sock_udp.close()
                time.sleep(1)
                sys.exit()
        breathe_status = breathe(
            auth_host_ip, auth_mac_address, auth_ip, session, index, block)
        if breathe_status is False:
            if reconnet_enable == '1':
                print ('Breathe failed.Reconnecting...')
                time.sleep(10)
                session = []
                main()
            else:
                print ('Breathe failed...')
                sock_udp.close()
                time.sleep(1)
                sys.exit()


def conf_cr(filepath):
    ip = raw_input('local ip:')
    mac = raw_input('local mac address:')
    host_ip = search_server_ip(ip, mac)
    usr = raw_input("username:")
    pwd = raw_input("password:")
    service = search_service(mac, host_ip)
    version = raw_input("client_version(recommend 3.6.4):")
    message_disp = raw_input("display message?(0 or 1)")
    delay_login = raw_input("delay 10s to login?(0 or 1)")
    with open(filepath, 'w') as json_file:
        arg = {
            "auth_host_ip": host_ip,
            "ip": ip,
            "mac_address": mac,
            "username": usr,
            "password": pwd,
            "client_version": version,
            "service_type": service,
            "dhcp_setting": "0",
            "message_display_enable": message_disp,
            "delay_enable": delay_login,
            "reconnet_enable": "1"}
        json_file.write(json.dumps(arg))
    print ('Please restart the program!')
    sock_udp.close()
    sys.exit()


def load_init_config(filepath):
    #json_data = {}
    #filename = r'./esp_config.json'
    try:
        with open(filepath) as json_file:  # config file path
            try:
                json_data = json.load(json_file)
            except Exception, e:
                print(e)
                conf_cr(filepath)
        try:
            if json_data['auth_host_ip'] != '' and json_data['ip'] != '' and json_data['username'] != '' and json_data['password'] != '' and json_data['mac_address'] != '' and json_data['service_type'] != '' and json_data['client_version'] != '' and json_data['delay_enable'] != '' and json_data['dhcp_setting'] != '' and json_data['reconnet_enable'] != '' and json_data['message_display_enable'] != '':
                return json_data
            else:
                conf_cr(filepath)
        except Exception, e:
            print(e)
            conf_cr(filepath)
    except Exception, e:
        print(e)
        sys.exit(1)


if __name__ == '__main__':
    sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_udp.settimeout(5)
    if len(sys.argv) == 3:
        if sys.argv[1] == '-c':
            data = load_init_config(sys.argv[2])
            auth_host_ip = data['auth_host_ip']
            auth_ip = data['ip']
            auth_mac_address = data['mac_address']
            username = data['username']
            password = data['password']
            client_version = data['client_version']
            service_type = data['service_type']
            dhcp_setting = data['dhcp_setting']
            message_display_enable = data['message_display_enable']
            delay_enable = data['delay_enable']
            reconnet_enable = data['reconnet_enable']
            try:
                sock_udp.bind((auth_ip, 3848))
            except socket.error:
                print ('Bind port failed.Use random port')
            print ('Try to login in...')
            main()
        print('Usage:\t[option]\n\t-c filepath | set config file path')
    else:
        print('Usage:\t[option]\n\t-c filepath | set config file path')