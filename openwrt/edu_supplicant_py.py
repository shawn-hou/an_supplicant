# any question please read Swiftz Protocal for details
# codes start from main()

import hashlib
import struct
import time
import socket
import json
import os
import sys

# translate ascii data to unsigned char data which is necessary e.g. 172 for 0xAC, return str
def pack(data):
    return ''.join([struct.pack('B',i) for i in data])

# translate unsigned char data to ascii data e.g. 0xAC for 172, return [int, ...]
def unpack(data):
    return [i for i in struct.unpack('B' * len(data), data)]

# feed pkg with md5 valve, return [int, ...]
def md5_to_pkg(pkg):
    data = pack(pkg)
    md5_valve = hashlib.md5(data).digest()
    pkg[2:18] = unpack(md5_valve)
    return pkg

# crypto3848 algorithm, return[int, ...]
def encrypt(data):
    for i in range(len(data)):
        data[i] = (data[i] & 0x80) >> 6 | (data[i] & 0x40) >> 4 | (data[i] & 0x20) >> 2 | (data[i] & 0x10) << 2 | (data[i] & 0x08) << 2 | (data[i] & 0x04) << 2 | (data[i] & 0x02) >> 1 | (data[i] & 0x01) << 7
    return data

# crypto3848 algorithm, return[int, ...]
def decrypt(data):
    for i in range(len(data)):
        data[i] = (data[i] & 0x80) >> 7 | (data[i] & 0x40) >> 2 | (data[i] & 0x20) >> 2 | (data[i] & 0x10) >> 2 | (data[i] & 0x08) << 2 | (data[i] & 0x04) << 4 | (data[i] & 0x02) << 6 | (data[i] & 0x01) << 1
    return data

# generate a package for breathe, return str
def generate_breathe_pkg(mac, ip, session, index_data):
    pkg = []
    pkg.append(3)                                 # 3 for 0x03 means breathe Action Code
    pkg_len = len(session) + 88                   # 88 = 1+1+16+2+18+8+6+6*6
    pkg.append(pkg_len)
    pkg.extend([i * 0 for i in range(16)])
    pkg.extend([8, len(session) + 2])             # 8 for 0x08 means session Field Code
    pkg.extend(session)
    pkg.extend([9, 18])                           # 0x09 for ip Field Code, 18 for length
    pkg.extend([ord(i) for i in ip])
    pkg.extend([i * 0 for i in range(16 - len(ip))])
    pkg.extend([7, 8])                            # 0x07 for mac Field Code, 8 for length
    pkg.extend([int(i, 16) for i in mac.split(':')])
    pkg.extend([20, 6])                           # 0x14 for index Field Code, 6 for length
    index_data = hex(index_data)[2:]              # a = hex(69) => a = '0x45' , a = a[2:] => a = '45'
    pkg.extend([int(index_data[0:-6],16), int(index_data[-6:-4],16), int(index_data[-4:-2],16), int(index_data[-2:],16)])
    # unknown data but necessary for breathe
    pkg.extend([42, 6, 0, 0, 0, 0, 43, 6, 0, 0, 0, 0, 44, 6, 0, 0, 0, 0, 45, 6, 0, 0, 0, 0, 46, 6, 0, 0, 0, 0, 47, 6, 0, 0, 0, 0])
    pkg = md5_to_pkg(pkg)                         # feed md5 valve to pkg
    pkg = encrypt(pkg)                            # encrypt it
    pkg = pack(pkg)                               # pack it to Byte data e.g. 172 for 0xAC
    return pkg

# breathe function, return none
def breathe(sock, server, mac, ip, session, index_data):
    time.sleep(2)                                # this line just run once when the function called
    while True:
        print r'breathe starting!'
        breathe_pkg = generate_breathe_pkg(mac, ip, session, index_data)
        sock.sendto(breathe_pkg, (server, 3848))
        try:
            breathe_ret = sock.recv(4096)
        except socket.timeout:                    # resend when timeout
            print r'breathe time out...continue...'
            continue
        else:
            status = unpack(breathe_ret)[20]
            if status == 0:                       # check connection status
                print r'breathe failed...exiting...'
                sock.close()
                break                             # exit breathe loop
            else:
                print r'breathe successful! waiting...'
                index_data += 3                   # index increases 3 every valid breathe
                time.sleep(25)                    # breathe every 25 seconds

# generate a package for login action, return str
def generate_login_pkg(mac, ip, user, password, service_type, version):
    pkg = []
    pkg.append(1)                                 # 1 for 0x01 means login Action Code
    pkg_len = len(user)+len(password)+len(ip)+len(service_type)+44  # 44 = 1+1+16+8+2+2+2+2+3+7
    pkg.append(pkg_len)
    pkg.extend([i * 0 for i in range(16)])        # blank field for MD5 valve
    pkg.extend([7, 8])                            # 0x07 for MAC Field Code, 8 for length
    pkg.extend([int(i, 16) for i in mac.split(':')])
    pkg.extend([1, len(user) + 2])                # 0x01 for user Field Code
    pkg.extend([ord(i) for i in user])
    pkg.extend([2, len(password) + 2])            # 0x02 for password Field Code
    pkg.extend([ord(i) for i in password])
    pkg.extend([9, len(ip) + 2])                  # 0x09 for ip Field Code
    pkg.extend([ord(i) for i in ip])
    pkg.extend([10, len(service_type) + 2])       # 0x0A for service type Field Code
    pkg.extend(service_type)
    pkg.extend([14, 3, 0])  # 0x0E for dhcp(0), 0x1F for version(3.6.2)
    pkg.extend([0x1f, len(version) + 2])
    pkg.extend([ord(i) for i in version])
    pkg = md5_to_pkg(pkg)                         # feed md5 valve to pkg
    pkg = encrypt(pkg)                            # encrypt it
    pkg = pack(pkg)                               # pack it to Byte data e.g. 172 for 0xAC
    return pkg

# login function, return [int, [int, ...]]
def login(sock, server, mac, ip, user, password, service_type, version):
    print r'server ip:'
    print server
    print r'mac:'
    print mac
    print r'ip:'
    print ip
    print r'service type:'
    print service_type
    login_pkg = generate_login_pkg(mac, ip, user, password, service_type, version)
    sock.sendto(login_pkg, (server, 3848))        #server:3848 Swiftz Protocal
    try:
        login_ret = sock.recv(4096)
    except socket.timeout:                        # timeout return [0, 0]
        print r'login time out...'
        status = 0
        session = 0
        return [status, session]
    else:
        login_ret = unpack(login_ret)             # unpack it
        decrypt(login_ret)                        # decrypt it
        status = login_ret[20]                    # 18~20 for success field 20 for success status
        session_len = login_ret[22]               # 21~23 for session field
        session = login_ret[23:session_len + 23]  # get session from session field
        return [status, session]

# generate a package for search service type, return str
def generate_search_service_pkg(mac):
    pkg = []
    pkg.append(7)                                 # 0x07 for search service type Action Code
    pkg_len = 48                                  # package length, 48 = 1 + 1 + 16 + 12 + 18
    pkg.append(pkg_len)
    pkg.extend([i*0 for i in range(16)])          # blank for md5
    pkg.extend([8, 12])                           # 0x08 for session Field Code, 12 for field length
    pkg.extend([i*0 for i in range(10)])          # session is 10 '0' here
    pkg.extend([7, 18])                           # 0x07 for mac Field Code, 18 for field length
    pkg.extend([int(i,16) for i in mac.split(':')])
    pkg.extend([i*0 for i in range(10)])          # mac length is 6, so 10 ascii '0' can fill the field
    pkg = md5_to_pkg(pkg)                         # feed md5 to package
    pkg = encrypt(pkg)                            # encrypt it
    pkg = pack(pkg)                               # pack it to Byte data e.g. 172 for 0xAC
    return pkg

# function for searching service type, return [int, [int, ...]]
def search_service_type(sock, server, mac):
    search_service_type_pkg = generate_search_service_pkg(mac)
    sock.sendto(search_service_type_pkg, (server, 3848))        # server:3848, Swiftz Protocal
    try:
        search_service_type_ret = sock.recv(4096)
    except socket.timeout:
        status = 0
        service_type = ''
        return [status, service_type]
    else:
        search_service_type_ret = unpack(search_service_type_ret)
        search_service_type_ret = decrypt(search_service_type_ret)
        search_service_type_ret[2:18] = [i * 0 for i in range(16)]
        service_type_index = search_service_type_ret.index(10) + 2  # [18:] avoid md5 interference
        service_type_len = search_service_type_ret[service_type_index - 1]  # get target area length
        service_type = search_service_type_ret[service_type_index:service_type_index+service_type_len]
        status = 1
        return [status, service_type]

# generate a package for search server ip, return str
def generate_search_server_ip_pkg(mac, ip):
    pkg = []
    pkg.append(12)                                # 0x0C for search server ip Action Code
    pkg_len = 66                                  # package length, 66 = 1 + 1 + 16 + 12 + 18 + 18
    pkg.append(pkg_len)
    pkg.extend([i*0 for i in range(16)])          # blank for md5 which length is 16
    pkg.extend([8, 12])                           # 0x08 for session Field Code, 12 for field length
    pkg.extend([i*0 for i in range(10)])          # session is 10 '0' here
    pkg.extend([9, 18])                           # 0x09 for ip Field Code, 18 for field length
    pkg.extend([ord(i) for i in ip])
    pkg.extend([i*0 for i in range(16-len(ip))])  # fill the rest of field with ascii '0'
    pkg.extend([7, 18])                           # 0x07 for mac Field Code, 18 for field length
    pkg.extend([int(i,16) for i in mac.split(':')])
    pkg.extend([i*0 for i in range(10)])          # mac length is 6, so 10 ascii '0' can fill the field
    pkg = md5_to_pkg(pkg)                         # feed md5 to package
    pkg = encrypt(pkg)                            # encrypt it
    pkg = pack(pkg)                               # pack it to Byte data e.g. 172 for 0xAC
    return pkg

# function for searching server ip, return [int, str]
def search_server_ip(sock, mac, ip):
    search_server_ip_pkg = generate_search_server_ip_pkg(mac, ip)
    sock.sendto(search_server_ip_pkg, ('1.1.1.8', 3850))
    try:                                          # '1.1.1.8:3850' used to search ip, Swiftz Protocal
        search_server_ip_ret = sock.recv(4096)
    except socket.timeout:                        # if it is time out
        status = 0
        server_ip = ''
        return [status, server_ip]
    else:                                         # unpack, decrypt and acquire server ip that you want
        search_server_ip_ret = unpack(search_server_ip_ret)
        search_server_ip_ret = decrypt(search_server_ip_ret)
        server_ip = search_server_ip_ret[20:24]   # 20:24 is the server ip data index in recv package
        server_ip = '.'.join([str(i) for i in server_ip]) # [172, 168, 124, 126] to '172.168.124.126'
        status = 1
        return [status, server_ip]

# auto connect, include search server ip, search service tpye, login and breathe, return none
def auto_connect(mac, ip, user, password, version):
    print r'connect starting...'
    index_data = 0x01000000                       # breathe counter
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(10)                           # set time out to 10 seconds
    try:
        sock.bind((ip, 3848))
    except socket.error:
        print ('Bind port failed.Use random port')
        pass
    # first, search valid server ip
    search_server_ip_retrun = search_server_ip(sock, mac, ip)
    while search_server_ip_retrun[0] == 0:        # check if return invaild
        print r'search server ip failed! researching...'
        time.sleep(5)
        search_server_ip_retrun = search_server_ip(sock, mac, ip)
    server = search_server_ip_retrun[1]           # get server ip successful
    print r'server ip get!'

    # next, search valid service type, some schools use 'int', some use 'internet', etc
    search_service_type_return = search_service_type(sock, server, mac)
    while search_service_type_return[0]  == 0:
        print r'search service type failed! researching...'
        time.sleep(5)
        search_service_type_return = search_service_type(sock, server, mac)
    service_type = search_service_type_return[1]  # get service type successful
    print r'service type get!'

    # next, login
    login_return = login(sock, server, mac, ip, user, password, service_type, version)
    while login_return[0] == 0:                   # check if it login successful
        print r'login failed! relogining...'
        time.sleep(5)
        login_return = login(sock, server, mac, ip, user, password, service_type, version)
    session = login_return[1]                     # get session successful
    print r'login successful!'
    # finally, breathe to keep connection alive
    breathe(sock, server, mac, ip, session, index_data)

# use linux shell to acquire local mac and ip, return [int, str, str]
def search_local_mac_ip():
    counter = 0                                       # counter times to limit
    while counter < 20:                               # timeout limit = 20 * 0.5 = 10s
        data = os.popen("ifconfig | grep -B1 'inet\ addr' | awk 'NF==5{print $5};NF==4{print $2}' | grep -v '\.1$' | grep -v 'addr:169\.254' | grep -B1 'addr'").read()     # shell script
        if len(data) != 0:                            # if mac ip data not exist
            status = 1
            mac = data[:17]                           # mac index in str that linux shell return
            ip = data[23:-1]                          # ip index in str that linux shell return
            break
        else:
            counter += 1
            time.sleep(0.5)
    if counter == 20:                                 # time out
            status = 0
            mac = ''
            ip = ''
    return [status, mac, ip]

# function for using config file, return dict that contains 'ip' 'mac' 'user' 'password'
def load_config(abs_path):
    try:
        with open(abs_path) as json_file:    # you can set config file name and path here
            data = json.load(json_file)
    except:                                       # if read config file failed
        print r'invaild input! please check the absolute path of your config file'
        sys.exit()
    else:
        return data

# start
def main():
    # run with argv
    if len(sys.argv) > 1:
        if sys.argv[1] == '-h':
            print '-c with the absolute path of your config file e.g. /root/config.json'
            sys.exit()
        elif sys.argv[1] == '-c':
            data = load_config(sys.argv[2])
    else:
        print 'invaild operation! run with -h can show more usages'
        sys.exit()
    delay = data['delay']
    if delay == '1':
        time.sleep(20)
    macip_data = search_local_mac_ip()
    if macip_data[0] == 1:                        # auto acquire mac and ip
        mac = macip_data[1]
        ip = macip_data[2]
    else:                                         # if auto acquire failed, load config file
        mac = data['mac']
        ip = data['ip']
    user = data['user']
    password = data['password']
    version = data['version']
    while True:                                   # restart when breathe failed
        auto_connect(mac, ip, user, password, version)

if __name__ == '__main__':
    main()
