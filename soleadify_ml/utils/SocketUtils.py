from socket import socket, AF_INET, SOCK_STREAM


def connect(soc, host, port):
    try:
        soc.connect((host, port))
        return True
    except:
        return False


def recv_end(soc):
    total_data = []
    end = '--end--'
    while True:
        data = soc.recv(8192).decode('utf8')
        if not data:
            break
        if end in data:
            total_data.append(data[:data.find(end)])
            break
        total_data.append(data)
        if len(total_data) > 1:
            # check if end_of_data was split
            last_pair = total_data[-2] + total_data[-1]
            if end in last_pair:
                total_data[-2] = last_pair[:last_pair.find(end)]
                total_data.pop()
                break
    return ''.join(total_data)


def socket_bind(host, port):
    num_port_socks = 2
    main_socks, read_socks, write_socks = [], [], []
    for i in range(num_port_socks):
        port_sock = socket(AF_INET, SOCK_STREAM)
        port_sock.bind((host, port))
        port_sock.listen(5)
        main_socks.append(port_sock)
        read_socks.append(port_sock)
        port += 1

    return main_socks, read_socks, write_socks
