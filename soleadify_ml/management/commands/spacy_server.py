import hashlib
import logging
import spacy
from django.conf import settings
from django.core.management.base import BaseCommand
import json
import re
from select import select
from spacy.tokens.span import Span

from soleadify_ml.models.website_contact_meta import WebsiteContactMeta
from soleadify_ml.utils.SocketUtils import recv_end, socket_bind

logger = logging.getLogger('spacy')


class Command(BaseCommand):
    help = 'spacy server'
    line_numbers = []

    def handle(self, *args, **options):
        spacy_model = spacy.load(settings.SPACY_CUSTOMN_MODEL_FOLDER, disable=['parser', 'tagger', 'textcat'])
        Span.set_extension('is_phone', getter=Command.is_phone_getter, force=True)
        Span.set_extension('line_number', getter=Command.line_number_getter, force=True)

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
        line_numbers = [x.start() for x in re.finditer('\n', token.doc.text)]
        for key, line_no in enumerate(line_numbers):
            if start_char < line_no:
                return key
        return len(line_numbers)

    @staticmethod
    def get_ent(current_entity):
        text = current_entity.text
        if len(text) <= 2:
            return None

        if current_entity.label_ == 'EMAIL':
            if not current_entity.root.like_email:
                return None

        if current_entity.label_ == 'PHONE':
            text = re.sub('\D', '', text)
            if not current_entity._.get('is_phone'):
                return None

            if len(text) <= 7:
                return None

        return {'label': current_entity.label_, 'text': text.strip(), 'start': current_entity.start,
                'end': current_entity.end, 'line_no': current_entity._.get('line_number')}

    @staticmethod
    def get_entities(spider, text, url):
        new_docs = []
        Command.line_numbers = []
        if not text:
            return new_docs
        dom_element_text_key = hashlib.md5(text.encode()).hexdigest()
        try:
            if dom_element_text_key in spider.cached_docs:
                docs = spider.cached_docs[dom_element_text_key]
            else:
                spider.soc_spacy.sendall(text.encode('utf8') + '--end--'.encode('utf8'))
                docs = json.loads(recv_end(spider.soc_spacy))
                spider.cached_docs[dom_element_text_key] = docs
        except Exception as ve:
            logger.error("%s : %s", url, ve)
            return new_docs

        for doc in docs:
            # if the phone is not valid for the country ignore it
            if doc['label'] == 'PHONE':
                valid_phone = WebsiteContactMeta.get_valid_country_phone(spider.country_codes, doc['text'])
                if valid_phone:
                    doc['text'] = valid_phone
                else:
                    continue
            new_docs.append(doc)

        return new_docs
