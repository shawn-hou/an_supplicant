# any question please read Swiftz Protocal for details
# codes start from main()

import hashlib
import struct
import time
import socket
import sys
import json
import os
import netifaces

# translate ascii data to unsigned char data which is necessary e.g. 172 for 0xAC, return str
def pack(data):
    return ''.join([struct.pack('B',i) for i in data])

# translate unsigned char data to ascii data e.g. 0xAC for 172, return [int,...]
def unpack(data):
    return [i for i in struct.unpack('B' * len(data), data)]

# feed pkg with md5 valve, return [int, ...]
def md5_to_pkg(pkg):
    data = pack(pkg)
    md5_valve = hashlib.md5(data).digest()
    pkg[2:18] = unpack(md5_valve)
    return pkg

def check_md5(md5,md5_recv):
    for i in range(16):
        if md5[i] != md5_recv[i]:
            return False
    return True

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

# generate a package for login action, return str, untest
def generate_login_pkg(mac, ip, user, password, service_type, client_version):
    print 'generating login pkg...'
    pkg = []
    pkg.append(1)                                 # 1 for 0x01 means login Action Code
    pkg_len = len(user)+len(password)+len(ip)+len(service_type)+44
    pkg.append(pkg_len)
    pkg.extend([i * 0 for i in range(16)])        # blank field for MD5 valve
    pkg.extend([7, 8])                            # 7 for 0x07 means MAC Field Code, 8 means length
    pkg.extend([int(i, 16) for i in mac.split(':')])
    pkg.extend([1, len(user) + 2])                # 1 for 0x01 means user Field Code
    pkg.extend([ord(i) for i in user])
    pkg.extend([2, len(password) + 2])
    pkg.extend([ord(i) for i in password])
    pkg.extend([9, len(ip) + 2])
    pkg.extend([ord(i) for i in ip])
    pkg.extend([10, len(service_type) + 2])
    pkg.extend(service_type)
    pkg.extend([14, 3, 0])  #0x0e for dhcp disable, 0x1f for version 3.6.2
    pkg.extend([31, len(client_version) +2])
    pkg.extend([ord(i) for i in client_version])
    pkg = md5_to_pkg(pkg)                         # feed md5 valve to pkg
    pkg = encrypt(pkg)                            # encrypt it
    pkg = pack(pkg)                               # pack it to Byte data e.g. 172 for 0xAC
    print 'login pkg made...'
    return pkg

# login function, return [bool, [int, ...]], untest
def login(sock, server, mac, ip, user, password, service_type, client_version):
    print 'login start...'
    login_pkg = generate_login_pkg(mac, ip, user, password, service_type, client_version)
    sock.sendto(login_pkg, (server, 3848))        # send login package to the server:3848 for Protocal
    try:
        login_ret = sock.recv(4096)
    except socket.timeout:                        # timeout return [0, 0]
        status = False
        session = 0
        print 'timeout...'
        return [status, session]
    else:
        login_ret = unpack(login_ret)             # unpack it
        login_ret = decrypt(login_ret)                        # decrypt
        md5_recv = login_ret[2:18]
        login_ret[2:18] = [i*0 for i in range(16)]
        md5 = hashlib.md5(b''.join([struct.pack('B', i) for i in login_ret])).digest()
        md5 = struct.unpack('16B',md5)
        if check_md5(md5,md5_recv) is True:
            status = bool(login_ret[20])              # 18~20 for success field 20 for success status
            session_len = login_ret[22]               # 21~23 for session field
            session = login_ret[23:session_len + 23]  # get session from session field
            print 'return login list...'
            return [status, session]
        else:
            print 'md5 check error!'
            return [False,0]

# auto connect, include search server ip, search service tpye, login and breathe, return none, untest
def auto_connect(mac, ip, user, password, client_version):
    print 'auto connect program start...'
    index = 0x01000000
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((ip, 3848))
    # search valid server ip at first
    search_server_ip_retrun = search_server_ip(sock, mac, ip)
    print search_server_ip_retrun
    while search_server_ip_retrun[0] is not True:            # check vaild server ip
        print 'search server ip failed...research...'
        time.sleep(1.5)
        search_server_ip_retrun = search_server_ip(sock, mac, ip)
    server = search_server_ip_retrun[1]

    # search valid service type is the next
    search_service_type_return = search_service_type(sock, server, mac)
    while search_service_type_return[0] is not True:
        print 'search service type failed...research...'
        time.sleep(1.5)
        search_service_type_return = search_service_type(sock, server, mac)
    service_type = search_service_type_return[1]

    # when server ip get, login is the next
    login_return = login(sock, server, mac, ip, user, password, service_type, client_version)
    while login_return[0] is not True:                       # check connection status
        print 'login failed...relogin...'
        time.sleep(10)
        login_return = login(sock, server, mac, ip, user, password, service_type, client_version)
    session = login_return[1]
    print 'login success!'
    # when session get, breathe is the last thing
    breathe(sock, server, mac, ip, session, index)

# generate a package for breathe, return str, untest
def generate_breathe_pkg(mac, ip, session, index):
    index = hex(index)[2:]                        # a = hex(69) => a = '0x45' , a = a[2:] => a = '45'
    pkg = []
    pkg.append(3)                                 # 3 for 0x03 means breathe Action Code
    pkg_len = len(session) + 88
    pkg.append(pkg_len)
    pkg.extend([i * 0 for i in range(16)])
    pkg.extend([8, len(session) + 2])             # 8 for 0x08 means session Field Code
    pkg.extend(session)
    pkg.extend([9, 18])
    pkg.extend([ord(i) for i in ip])
    pkg.extend([i * 0 for i in range(16 - len(ip))])
    pkg.extend([7, 8])
    pkg.extend([int(i, 16) for i in mac.split(':')])
    pkg.extend([20, 6])
    pkg.extend([int(index[0:-6],16), int(index[-6:-4],16), int(index[-4:-2],16), int(index[-2:],16)])
    # unknown data but necessary for breathe
    pkg.extend([42, 6, 0, 0, 0, 0, 43, 6, 0, 0, 0, 0, 44, 6, 0, 0, 0, 0, 45, 6, 0, 0, 0, 0, 46, 6, 0, 0, 0, 0, 47, 6, 0, 0, 0, 0])
    pkg = md5_to_pkg(pkg)                         # feed md5 valve to pkg
    pkg = encrypt(pkg)                            # encrypt it
    pkg = pack(pkg)                               # pack it to Byte data e.g. 172 for 0xAC
    return pkg

# breathe function, return none, untest
def breathe(sock, server, mac, ip, session, index):
    time.sleep(2)                                # this line just run once when the function called
    print 'breathe start!'
    while True:
        breathe_pkg = generate_breathe_pkg(mac, ip, session, index)
        sock.sendto(breathe_pkg, (server, 3848))
        try:
            breathe_ret = sock.recv(4096)
        except socket.timeout:                    # resend when timeout
            time.sleep(0.1)
            continue
        else:
            breathe_ret = unpack(breathe_ret)
            breathe_ret = decrypt(breathe_ret)
            md5_recv = breathe_ret[2:18]
            breathe_ret[2:18] = [i*0 for i in range(16)]
            md5 = hashlib.md5(b''.join([struct.pack('B', i) for i in breathe_ret])).digest()
            md5 = struct.unpack('16B',md5)
            if check_md5(md5,md5_recv) is True:
                status = breathe_ret[20]            
                if status == 0:                       # check connection status
                    sock.close()
                    session =[]
                    break
                else:
                    index += 3                        # index increases 3 every valid breathe
                    time.sleep(20)                    # breathe every 25 seconds
            else:
                print 'md5 check error!'
                sock.close()
                session =[]
                break

# generate a package for search server ip, return str, untest
def generate_search_server_ip_pkg(mac, ip):
    pkg = []
    pkg.append(12)
    pkg_len = 66                                  # 1 + 1 + 16 + 12 + 18 + 18
    pkg.append(pkg_len)
    pkg.extend([i*0 for i in range(16)])
    pkg.extend([8, 12])
    pkg.extend([i*0 for i in range(10)])          # 10 Byte ascii '0' for session
    pkg.extend([9, 18])
    pkg.extend([ord(i) for i in ip])
    pkg.extend([i*0 for i in range(16-len(ip))])  # ip length is not sure
    pkg.extend([7, 18])
    pkg.extend([int(i,16) for i in mac.split(':')])
    pkg.extend([i*0 for i in range(10)])          # mac length is 6
    pkg = md5_to_pkg(pkg)                         # feed md5 to package
    pkg = encrypt(pkg)                            # encrypt it
    pkg = pack(pkg)                               # pack it to Byte data e.g. 172 for 0xAC
    return pkg

# function for searching server ip, return [int, str], untest
def search_server_ip(sock, mac, ip):
    search_server_ip_pkg = generate_search_server_ip_pkg(mac, ip)
    sock.sendto(search_server_ip_pkg, ('1.1.1.8', 3850))
    try:                                          # '1.1.1.8:3850' used to search ip, docs for details
        search_server_ip_ret = sock.recv(4096)
    except socket.timeout:                        # timeout handle
        status = False
        server_ip = ''
        return [status, server_ip]
    else:                                         # unpack, decrypt and acquire server ip that you want
        search_server_ip_ret = unpack(search_server_ip_ret)
        search_server_ip_ret = decrypt(search_server_ip_ret)
        md5_recv = search_server_ip_ret[2:18]
        search_server_ip_ret[2:18] = [i*0 for i in range(16)]
        md5 = hashlib.md5(b''.join([struct.pack('B', i) for i in search_server_ip_ret])).digest()
        md5 = struct.unpack('16B',md5)
        if check_md5(md5,md5_recv) is True:
            server_ip = search_server_ip_ret[20:24]
            server_ip = '.'.join([str(i) for i in server_ip])
            status = True
            return [status, server_ip]
        else:
            print 'md5 check error!'
            return [False, '']

# generate a package for search service type, return str, untest
def generate_search_service_pkg(mac):
    print 'generating search service type pkg...'
    pkg = []
    pkg.append(7)
    pkg_len = 2+16+12
    pkg.append(pkg_len)
    pkg.extend([i*0 for i in range(16)])
    pkg.extend([8, 12])
    pkg.extend([i*0 for i in range(10)])          # 10 Byte ascii '0' for session
    pkg.extend([7, 18])
    pkg.extend([int(i,16) for i in mac.split(':')])
    pkg.extend([i*0 for i in range(10)])          # mac length is 6
    pkg = md5_to_pkg(pkg)                         # feed md5 to package
    pkg = encrypt(pkg)                            # encrypt it
    pkg = pack(pkg)                               # pack it to Byte data e.g. 172 for 0xAC
    print 'search service type pkg made...'
    return pkg

# function for searching service type, return [bool, [int, ...]], untest
def search_service_type(sock, server, mac):
    print 'searching service type...'
    search_service_type_pkg = generate_search_service_pkg(mac)
    sock.sendto(search_service_type_pkg, (server, 3848))
    try:
        search_service_type_ret = sock.recv(4096)
    except socket.timeout:
        status = False
        service_type = ''
        print('search service type time out...')
        return [status, service_type]
    else:
        search_service_type_ret = unpack(search_service_type_ret)
        search_service_type_ret = decrypt(search_service_type_ret)
        md5_recv = search_service_type_ret[2:18]
        search_service_type_ret[2:18] = [i*0 for i in range(16)]
        md5 = hashlib.md5(b''.join([struct.pack('B', i) for i in search_service_type_ret])).digest()
        md5 = struct.unpack('16B',md5)
        if check_md5(md5,md5_recv) is True:
            service_type_index = search_service_type_ret.index(10) + 2
            service_type_len = search_service_type_ret[service_type_index - 1]
            service_type = search_service_type_ret[service_type_index:service_type_index+service_type_len]
            status = True
            print 'return service type list...'
            return [status, service_type]
        else:
            print 'md5 check error!'
            return [False, '']

# function for creat config file
def conf_cr():
    usr = raw_input("username:")
    pwd = raw_input("password:")
    print 'which is your WAN netiface?'
    all_netifaces = netifaces.interfaces()
    print all_netifaces
    netiface = raw_input("netiface:")
    client_version = raw_input("client_version(recommend 3.6.4):")
    with open('esp_config.json','w') as json_file:
        arg = {"user":usr,"password":pwd,"netiface":netiface,"version":client_version}
        json_file.write(json.dumps(arg))
    main()



# function for using config file, return dict that contains 'ip' 'mac' 'user' 'password'
def load_init_config():
    data = {}
    filename = r'esp_config.json'
    if os.path.exists(filename):
        with open('esp_config.json') as json_file:  # you can set config file name and path here
            try:
                data = json.load(json_file)
            except:
                conf_cr()
        return data
    else:
        conf_cr()

# start
def main():
    data = load_init_config()
    user = data['user']
    password = data['password']
    netiface = data['netiface']
    client_version = data['version']
    if user == '' or password == '' or netiface == '' or client_version == '':
        conf_cr()
    try:
        addrs = netifaces.ifaddresses(netiface)
        mac = addrs[netifaces.AF_LINK][0].values()[0]
        ip = addrs[netifaces.AF_INET][0].values()[2]
    except Exception,e:
        print e,"\nThe netifaces your selected had no IP or MAC!"
        sys.exit(1)
    while True:                               # restart when breathe failed
        auto_connect(mac, ip, user, password, client_version)

if __name__ == '__main__':
    main()
