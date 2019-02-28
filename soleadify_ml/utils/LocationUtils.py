import logging
from soleadify_ml.utils.SocketUtils import recv_end
import json
import re
import collections
import time
from geograpy.places import PlaceContext

logger = logging.getLogger(__name__)

stop_regions = {
    'city': ['sign', 'home', 'shop', 'us', 'about', 'unknown', 'industry', 'other', 'welcome', 'contact', 'jobs', 'job',
             'staff', 'chesapeake', 'find', 'laboratory', 'services', 'email', 'register', 'company', 'locate',
             'zip', 'close', 'else', 'city', 'make', 'model', 'yes', 'login', 'location', 'are', 'share', 'log',
             'hours', 'remember', 'force', 'cart', 'our', 'telephone', 'posts', 'those', 'sort', 'many', 'even'],
    'country': ['at', 'by', 'to'],
    'state': ['follow', 'at', 'by', 'to', 'and'],
    'city_district': [],
    'suburb': []
}
keys = ['suburb', 'city_district', 'city', 'state', 'country']
pc = PlaceContext('')
db_locations = {}
secondary_keys = ['house_number', 'road', 'unit', 'po_box', 'postcode', 'suburb']
ignored = ['house', 'near', 'category', 'level', 'island', 'country_region', 'world_region']


def get_key(dict_keys, loc):
    loc_key = ''
    for _key in dict_keys:
        if _key in loc:
            loc_key += loc[_key]

    return loc_key


def get_verified_address(_single_address):
    db_location_key = get_key(keys, _single_address)

    if db_location_key in db_locations:
        _address = db_locations[db_location_key]
    else:
        _address = pc.get_location(_single_address.copy())

        if not _address and 'city' in _single_address and "city" in _single_address['city']:
            _single_address['city'] = _single_address['city'].replace('city', '')

        _address = pc.get_location(_single_address.copy())

        if not _address and 'country' in _single_address and 'state' in _single_address:
            for location_type in ['city', 'city_district', 'suburb']:
                if location_type in _single_address:
                    _single_address.pop(location_type, None)
                    _address = pc.get_location(_single_address.copy())

                    if _address:
                        break

        db_locations[db_location_key] = _address

    return _address


def is_valid(_addresses, saved_address, saved_sentences):
    if len(_addresses) == 1 and _addresses[0][1] in ['house', 'suburb']:
        saved_address.append(None)
        saved_sentences.append(None)
        return False

    for address in _addresses:
        if address[1] in keys:

            address_key = re.sub("[^\\w| ]", "", address[0]).strip()

            if address_key in stop_regions[address[1]]:
                saved_address.append(None)
                saved_sentences.append(None)
                return False
        if address[1] == 'city':
            address_key = re.sub("[^\\w| ]", "", address[0]).strip()
            if len(address_key) <= 2:
                saved_address.append(None)
                saved_sentences.append(None)
                return False

    return True


def add_to_final_locations(_verified_address, _locations):
    _key = _verified_address['country_code'] + _verified_address['region_code']

    if 'city' in _verified_address:
        _key += _verified_address['city']
    if _key not in _locations or len(_locations[_key].values()) < len(_verified_address.values()):
        _verified_address['occurrences'] = 1
        _locations[_key] = _verified_address

    elif _key in _locations:
        _locations[_key]['occurrences'] += 1


def set_country_code(single_address, country_code):
    _key_intersect = list(set(single_address.keys()) & set(keys))
    _secondary_key_intersect = list(set(single_address.keys()) & set(secondary_keys))
    if country_code and 'country' not in single_address and len(_key_intersect) > 0 and len(
            _secondary_key_intersect) > 0:
        single_address['country'] = country_code


def get_location(soc, text, country_code):
    final_locations = {}
    unverified_locations = {}

    saved_address = collections.deque(maxlen=3)
    saved_sentences = collections.deque(maxlen=3)

    saved_socks = {}
    t2 = 0

    sentences = text.split('\n')
    for sentence in sentences:

        sentence = sentence.strip()

        sentence = re.sub("[^\\w.,-]", " ", sentence)
        sentence = re.sub(" +", " ", sentence)

        sentence_key = re.sub('[^A-Za-z]', '', sentence.lower())

        if len(sentence_key) <= 1:
            continue

        if sentence_key in saved_socks:
            address = saved_socks[sentence_key]
        else:
            soc.sendall(sentence.encode('utf8') + '--end--'.encode('utf8'))
            address = json.loads(recv_end(soc))
            saved_socks[sentence_key] = address

        if not is_valid(address, saved_address, saved_sentences):
            continue

        saved_address.append(address)
        saved_sentences.append(sentence)

        single_address = {}
        for locations in filter(None, list(saved_address)):
            single_address.update({value[1]: value[0].strip() for value in locations if value[1] not in ignored})

        set_country_code(single_address, country_code)
        key_intersect = list(set(single_address.keys()) & set(keys))
        secondary_key_intersect = list(set(single_address.keys()) & set(secondary_keys))

        verified_address = None
        unverified_address = None
        if len(key_intersect) > 1:
            t1 = time.time()
            verified_address = get_verified_address(single_address)
            t2 += time.time() - t1

        elif len(final_locations.values()) == 0 and len(key_intersect) > 0 and len(
                secondary_key_intersect) > 1 and 'city' in single_address:
            # this has been done to counter 'this has been done on 2014/25', which would have been translated to
            # nigeria, on, number: 2014...
            t1 = time.time()
            unverified_address = get_verified_address(single_address)
            t2 += time.time() - t1

        if verified_address or unverified_address:
            current_address = verified_address if verified_address else unverified_address
            for key in keys:
                if key in single_address:
                    single_address.pop(key, None)
            current_address.update(single_address)

            if verified_address:
                add_to_final_locations(current_address, final_locations)
            elif unverified_address:
                add_to_final_locations(current_address, unverified_locations)

            saved_address = collections.deque(maxlen=3)
            saved_sentences = collections.deque(maxlen=3)

    return_locations = []

    if len(final_locations.values()) > 0:
        return_locations = list(final_locations.values())
    elif len(unverified_locations) > 0:
        return_locations = list(unverified_locations.values())

    return return_locations
