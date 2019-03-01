import spacy
from django.conf import settings
from django.core.management.base import BaseCommand
import json
from select import select
from spacy.tokens.span import Span

from soleadify_ml.utils.SocketUtils import recv_end, socket_bind
from soleadify_ml.utils.SpiderUtils import is_phone_getter


class Command(BaseCommand):
    help = 'spacy server'

    def handle(self, *args, **options):

        spacy_model = spacy.load(settings.SPACY_CUSTOMN_MODEL_FOLDER)
        Span.set_extension('is_phone', getter=is_phone_getter, force=True)

        self.stdout.write("Loaded spacy server", ending='\n')
        main_socks, read_socks, write_socks = socket_bind('', 50010)
        while True:
            readable, writeable, exceptions = select(read_socks, write_socks, [])
            for sockobj in readable:
                if sockobj in main_socks:
                    new_sock, address = sockobj.accept()
                    print('Connect:', address, id(new_sock))
                    read_socks.append(new_sock)
                else:
                    try:
                        entities = []
                        data = recv_end(sockobj)
                        if not data:
                            sockobj.close()
                            read_socks.remove(sockobj)
                        else:
                            doc = spacy_model(data)

                            for ent in doc.ents:
                                if ent.label_ == 'ORG':
                                    pass

                                if ent.label_ == 'EMAIL':
                                    if not ent.root.like_email:
                                        continue

                                if ent.label_ == 'PHONE':
                                    if not ent._.get('is_phone'):
                                        continue

                                entities.append(
                                    {'label': ent.label_, 'text': ent.text, 'start': ent.start, 'end': ent.end})

                            sockobj.sendall(json.dumps(entities).encode('utf8') + '--end--'.encode('utf8'))
                    except:
                        pass