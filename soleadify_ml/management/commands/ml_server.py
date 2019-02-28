from django.core.management.base import BaseCommand
from soleadify_ml.utils import MLUtils
from soleadify_ml.models.category_website_text import CategoryWebsiteText
import json
import time
from select import select

from soleadify_ml.utils.SocketUtils import recv_end, socket_bind


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        self.stdout.write(str(time.time()), ending='\n')
        self.stdout.write("Starting server", ending='\n')
        self.stdout.write("Loading model", ending='\n')
        categories = CategoryWebsiteText.load_ml_data()
        MLUtils.prepare(categories)
        self.stdout.write("Model loaded", ending='\n')
        self.stdout.write(str(time.time()), ending='\n')
        main_socks, read_socks, write_socks = socket_bind('', 50008)

        while True:
            readable, writeable, exceptions = select(read_socks, write_socks, [])
            for sock_obj in readable:
                if sock_obj in main_socks:
                    new_sock, address = sock_obj.accept()
                    print('Connect:', address, id(new_sock))
                    read_socks.append(new_sock)
                else:
                    try:
                        data = recv_end(sock_obj)
                        if not data:
                            sock_obj.close()
                            read_socks.remove(sock_obj)
                        else:
                            res = MLUtils.predict_category(data)
                            sock_obj.sendall(json.dumps(res).encode('utf8') + '--end--'.encode('utf8'))
                    except:
                        pass
