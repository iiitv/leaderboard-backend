import codecs

from django.conf import settings
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser as DRFJSONParser
from rest_framework.utils import json


class JSONParser(DRFJSONParser):

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as JSON and returns the resulting data.
        """
        parser_context = parser_context or {}
        encoding = parser_context.get('encoding', settings.DEFAULT_CHARSET)
        request = parser_context.get('request')
        try:
            decoded_stream_data = codecs.getreader(encoding)(stream).read()
            # setting original body to request as raw_body, as it can't be read again
            setattr(request, 'raw_body', decoded_stream_data)
            parse_constant = json.strict_constant if self.strict else None
            return json.loads(decoded_stream_data, parse_constant=parse_constant)
        except ValueError as exc:
            raise ParseError('JSON parse error - %s' % str(exc))
