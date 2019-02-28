from django.core.management.base import BaseCommand
import json
from select import select
from postal.parser import parse_address
from soleadify_ml.utils.SocketUtils import recv_end, socket_bind


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        self.stdout.write("Loaded location server", ending='\n')
        main_socks, read_socks, write_socks = socket_bind('', 50006)
        while True:
            readable, writeable, exceptions = select(read_socks, write_socks, [])
            for sockobj in readable:
                if sockobj in main_socks:
                    new_sock, address = sockobj.accept()
                    print('Connect:', address, id(new_sock))
                    read_socks.append(new_sock)
                else:
                    try:
                        data = recv_end(sockobj)
                        if not data:
                            sockobj.close()
                            read_socks.remove(sockobj)
                        else:
                            new_data = parse_address(data)
                            sockobj.sendall(json.dumps(new_data).encode('utf8') + '--end--'.encode('utf8'))
                    except:
                        pass
