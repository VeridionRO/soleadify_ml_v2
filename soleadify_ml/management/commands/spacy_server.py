import logging
import spacy
from django.conf import settings
from django.core.management.base import BaseCommand
import json
import re
from select import select

from spacy.tokens.doc import Doc
from spacy.tokens.span import Span
from soleadify_ml.utils.SocketUtils import recv_end, socket_bind
from soleadify_ml.utils.SpiderUtils import check_email

logger = logging.getLogger('spacy')


class Command(BaseCommand):
    help = 'spacy server'

    def handle(self, *args, **options):
        spacy_model = spacy.load(settings.SPACY_CUSTOMN_MODEL_FOLDER, disable=['parser', 'tagger', 'textcat'])
        Span.set_extension('is_phone', getter=Command.is_phone_getter, force=True)
        Span.set_extension('line_number', getter=Command.line_number_getter, force=True)
        Doc.set_extension('lines', getter=Command.get_lines, setter=Command.set_lines)
        Doc.set_extension('_lines', default=list())

        logger.debug("Loaded spacy server")
        main_socks, read_socks, write_socks = socket_bind('', settings.SPACY_PORT)
        while True:
            readable, writeable, exceptions = select(read_socks, write_socks, [])
            for sockobj in readable:
                if sockobj in main_socks:
                    new_sock, address = sockobj.accept()
                    logger.debug('Connect: %s - %s', address, id(new_sock))
                    read_socks.append(new_sock)
                else:
                    try:
                        entities = []
                        data = recv_end(sockobj)
                        if not data:
                            sockobj.close()
                            read_socks.remove(sockobj)
                        else:
                            for doc in spacy_model.pipe([data]):
                                doc._.lines = [x.start() for x in re.finditer('\n', doc.text)]
                                for ent in doc.ents:
                                    current_entity = self.get_ent(ent)
                                    entities.append(current_entity) if current_entity else None

                            sockobj.sendall(json.dumps(entities).encode('utf8') + '--end--'.encode('utf8'))
                    except:
                        pass

    @staticmethod
    def is_phone_getter(token):
        pattern = re.compile("([\+|\(|\)|\-| |\.|\/]*[0-9]{1,9}[\+|\(|\)|\-| |\.|\/]*){7,}")
        if pattern.match(token.text):
            return True
        else:
            return False

    @staticmethod
    def line_number_getter(token):
        start_char = token.start_char
        line_numbers = token.doc._.lines
        # line_numbers = [x.start() for x in re.finditer('\n', token.doc.text)]
        for key, line_no in enumerate(line_numbers):
            if start_char < line_no:
                return key
        return len(line_numbers)

    @staticmethod
    def get_lines(doc):
        return doc._._lines

    @staticmethod
    def set_lines(doc, value):
        doc._._lines = value

    @staticmethod
    def get_ent(current_entity):
        text = current_entity.text
        if len(text) <= 2:
            return None

        if current_entity.label_ == 'EMAIL':
            text = text.lower()
            if not current_entity.root.like_email:
                return None

        if current_entity.label_ == 'PHONE':
            text = re.sub('\D', '', text)
            if not current_entity._.get('is_phone'):
                return None

            if len(text) <= 7:
                return None

            if not check_email(text):
                return None

        return {'label': current_entity.label_, 'text': text.strip(), 'start': current_entity.start,
                'end': current_entity.end, 'line_no': current_entity._.get('line_number')}
