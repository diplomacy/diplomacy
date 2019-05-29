# ==============================================================================
# Copyright (C) 2019 - Philip Paquette
#
#  This program is free software: you can redistribute it and/or modify it under
#  the terms of the GNU Affero General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option) any
#  later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
#  FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
#  details.
#
#  You should have received a copy of the GNU Affero General Public License along
#  with this program.  If not, see <https://www.gnu.org/licenses/>.
# ==============================================================================
""" Daide Clauses - Contains clauses that can be used to build / parse requests and responses """
from abc import ABCMeta, abstractmethod
import logging
import diplomacy.daide as daide
from diplomacy.daide.tokens import Token

# Constants
LOGGER = logging.getLogger(__name__)

def break_next_group(daide_bytes):
    """ If the next token is a parenthesis, finds its matching closing parenthesis and returns a tuple of the items
        between parentheses and the items after the closing parenthesis.
        e.g. bytes for (ENG AMY PAR) MTO NWY would return --> (ENG AMY PAR) + MTO NWY
        e.g. bytes for ENG AMY PAR would return -> '' + ENG AMY PAR since the byte array does not start with a "("

        :return: A tuple consisting of the parenthesis group and the remaining bytes after the group
                 or an empty byte array and the entire byte array if the byte array does not start with a parenthesis
    """
    if not daide_bytes:
        return b'', b''

    # Finding the matching closing parenthesis
    pos = 0
    parentheses_level = 0
    while True:
        if daide_bytes[pos:pos + 2] == bytes(daide.tokens.OPE_PAR):
            parentheses_level += 1
        elif daide_bytes[pos:pos + 2] == bytes(daide.tokens.CLO_PAR):
            parentheses_level -= 1
        if parentheses_level <= 0:
            break
        if pos >= len(daide_bytes):                         # Parentheses don't match - Not returning group
            pos = 0
            break
        pos += 2

    # Returning
    return (daide_bytes[:pos + 2], daide_bytes[pos + 2:]) if pos else (None, daide_bytes)

def strip_parentheses(daide_bytes):
    """ Removes parentheses from the DAIDE bytes and returns the inner content.
        The first and last token are expected to be parentheses.
    """
    assert daide_bytes[:2] == bytes(daide.tokens.OPE_PAR), 'Expected bytes to start with "("'
    assert daide_bytes[-2:] == bytes(daide.tokens.CLO_PAR), 'Expected bytes to end wth ")"'
    return daide_bytes[2:-2]

def parse_bytes(clause_constructor, daide_bytes, on_error='raise'):
    """ Creates a clause object from a string of bytes
        :param clause_constructor: The type of clause to build
        :param daide_bytes: The bytes to use to build this clause
        :param on_error: The action to take when an error is encountered ('raise', 'warn', 'ignore')
        :return: A tuple of 1) the clause object, and 2) the remaining (unparsed) bytes
    """
    assert on_error in ('raise', 'warn', 'ignore'), 'Valid values for error are "raise", "warn", "ignore"'
    clause = clause_constructor()
    daide_bytes = clause.from_bytes(daide_bytes, on_error=on_error)
    if not clause.is_valid:
        return None, daide_bytes
    return clause, daide_bytes

class AbstractClause(metaclass=ABCMeta):
    """ Abstract version of a DAIDE clause """
    def __init__(self):
        """ Constructor """
        self._is_valid = True

    @property
    def is_valid(self):
        """ Indicates if the clause is valid (no errors were triggered) """
        return self._is_valid

    @abstractmethod
    def __bytes__(self):
        """ Define the DAIDE bytes representation """
        raise NotImplementedError()

    @abstractmethod
    def from_bytes(self, daide_bytes, on_error='raise'):
        """ Builds the clause from a byte array
            :param daide_bytes: The bytes to use to build the clause
            :param on_error: The action to take when an error is encountered ('raise', 'warn', 'ignore')
            :return: The remaining (unparsed) bytes
        """
        raise NotImplementedError()

    def error(self, on_error, message=''):
        """ Performs the error action
            :param on_error: The action to take when an error is encountered ('raise', 'warn', 'ignore')
            :param message: The message to display
        """
        assert on_error in ('raise', 'warn', 'ignore'), 'Valid values for error are "raise", "warn", "ignore"'
        if on_error == 'raise':
            raise RuntimeError(message)
        if on_error == 'warn':
            LOGGER.warning(message)
        self._is_valid = False

class SingleToken(AbstractClause):
    """ Extracts a single token
        e.g. NME
    """
    def __init__(self):
        """ Constructor """
        super(SingleToken, self).__init__()
        self._bytes = b''
        self._str = ''

    def __bytes__(self):
        """ Define the DAIDE bytes representation """
        return self._bytes

    def __str__(self):
        """ Return the Diplomacy str """
        return self._str

    def from_bytes(self, daide_bytes, on_error='raise'):
        """ Builds the clause from a byte array
            :param daide_bytes: The bytes to use to build the clause
            :param on_error: The action to take when an error is encountered ('raise', 'warn', 'ignore')
            :return: The remaining (unparsed) bytes
        """
        token_bytes, remaining_bytes = daide_bytes[:2], daide_bytes[2:]

        # Not enough bytes to get a token
        if not token_bytes:
            self.error(on_error, 'At least 2 bytes are required to build a token.')
            return remaining_bytes

        # Getting the token
        self._bytes = token_bytes
        self._str = str(Token(from_bytes=token_bytes))
        return remaining_bytes

        # Getting the token
        self._bytes = bytes(Token(from_str=string))
        self._str = string

class Power(SingleToken):
    """ Each clause is a power
        Syntax: ENG
    """
    _alias_from_bytes = {'AUS': 'AUSTRIA',
                         'ENG': 'ENGLAND',
                         'FRA': 'FRANCE',
                         'GER': 'GERMANY',
                         'ITA': 'ITALY',
                         'RUS': 'RUSSIA',
                         'TUR': 'TURKEY'}

    def from_bytes(self, daide_bytes, on_error='raise'):
        """ Builds the clause from a byte array
            :param daide_bytes: The bytes to use to build the clause
            :param on_error: The action to take when an error is encountered ('raise', 'warn', 'ignore')
            :return: The remaining (unparsed) bytes
        """
        remaining_bytes = super(Power, self).from_bytes(daide_bytes, on_error)
        self._str = self._alias_from_bytes.get(self._str, self._str)
        return remaining_bytes

class String(AbstractClause):
    """ A string contained between parentheses
        Syntax (Text)
    """
    def __init__(self):
        """ Constructor """
        super(String, self).__init__()
        self._bytes = b''
        self._str = ''

    def __bytes__(self):
        """ Define the DAIDE bytes representation """
        return self._bytes

    def __str__(self):
        """ Return the Diplomacy str """
        return self._str

    def from_bytes(self, daide_bytes, on_error='raise'):
        """ Builds the clause from a byte array
            :param daide_bytes: The bytes to use to build the clause
            :param on_error: The action to take when an error is encountered ('raise', 'warn', 'ignore')
            :return: The remaining (unparsed) bytes
        """
        str_group_bytes, remaining_bytes = break_next_group(daide_bytes)

        # Can't find the string
        if not str_group_bytes:
            self.error(on_error, 'Unable to find a set of parentheses to extract the string clause.')
            return daide_bytes

        # Extract its content
        nb_bytes = len(str_group_bytes)
        self._bytes = str_group_bytes
        self._str = ''.join([str(Token(from_bytes=str_group_bytes[pos:pos + 2])) for pos in range(2, nb_bytes - 2, 2)])
        return remaining_bytes

class Number(AbstractClause):
    """ A number contained between parentheses
        Syntax: Number
    """
    def __init__(self):
        """ Constructor """
        super(Number, self).__init__()
        self._bytes = b''
        self._int = 0

    def __bytes__(self):
        """ Define the DAIDE bytes representation """
        return self._bytes

    def __str__(self):
        """ Return the Diplomacy str """
        return str(self._int)

    def __int__(self):
        """ Return the Diplomacy int """
        return self._int

    def from_bytes(self, daide_bytes, on_error='raise'):
        """ Builds the clause from a byte array
            :param daide_bytes: The bytes to use to build the clause
            :param on_error: The action to take when an error is encountered ('raise', 'warn', 'ignore')
            :return: The remaining (unparsed) bytes
        """
        if not daide_bytes:
            self.error(on_error, 'Expected at least 1 byte to parse a number')
            return daide_bytes

        number_bytes, remaining_bytes = daide_bytes[:2], daide_bytes[2:]
        number_token = Token(from_bytes=number_bytes)
        if not daide.tokens.is_integer_token(number_token):
            self.error(on_error, 'The token is not an integer. Got %s' % number_token)
            return daide_bytes

        # Extract its content
        self._bytes = number_bytes
        self._int = int(number_token)
        return remaining_bytes

class Province(AbstractClause):
    """ Each clause is an province token
        Syntax: ADR
                (STP ECS)
    """
    _alias_from_bytes = {'ECS': '/EC',
                         'NCS': '/NC',
                         'SCS': '/SC',
                         'WCS': '/WC',
                         'ECH': 'ENG',
                         'GOB': 'BOT',
                         'GOL': 'LYO'}

    def __init__(self):
        """ Constructor """
        super(Province, self).__init__()
        self._bytes = b''
        self._str = ''

    def __bytes__(self):
        """ Define the DAIDE bytes representation """
        return self._bytes

    def __str__(self):
        """ Return the Diplomacy str """
        return self._str

    def from_bytes(self, daide_bytes, on_error='raise'):
        """ Builds the clause from a byte array
            :param daide_bytes: The bytes to use to build the clause
            :param on_error: The action to take when an error is encountered ('raise', 'warn', 'ignore')
            :return: The remaining (unparsed) bytes
        """
        province_group_bytes, remaining_bytes = break_next_group(daide_bytes)

        # Is a province with coast
        # Syntax (STP NCS)
        if province_group_bytes:
            self._bytes = province_group_bytes

            province_group_bytes = strip_parentheses(province_group_bytes)
            province, province_group_bytes = parse_bytes(SingleToken, province_group_bytes, on_error=on_error)
            coast, province_group_bytes = parse_bytes(SingleToken, province_group_bytes, on_error=on_error)

            if province_group_bytes:
                self.error(on_error, '{} bytes remaining. Province is malformed'.format(len(province_group_bytes)))
                return daide_bytes

            str_province = self._alias_from_bytes.get(str(province), str(province))
            str_coast = self._alias_from_bytes.get(str(coast), str(coast))
            self._str = str_province + str_coast

        # Is a province with no coast
        # Syntax: ADR
        else:
            province, remaining_bytes = parse_bytes(SingleToken, remaining_bytes, on_error=on_error)
            self._bytes = bytes(province)
            self._str = self._alias_from_bytes.get(str(province), str(province))

        return remaining_bytes

class Turn(AbstractClause):
    """ Each clause is a Turn
        Syntax: (SPR 1901)
    """
    _alias_from_bytes = {'AUT': 'F.R',
                         'FAL': 'F.M',
                         'SPR': 'S.M',
                         'SUM': 'S.R',
                         'WIN': 'W.A'}

    def __init__(self):
        """ Constructor """
        super(Turn, self).__init__()
        self._bytes = b''
        self._str = ''

    def __bytes__(self):
        """ Define the DAIDE bytes representation """
        return self._bytes

    def __str__(self):
        """ Return the Diplomacy str """
        return self._str

    def from_bytes(self, daide_bytes, on_error='raise'):
        """ Builds the clause from a byte array
            :param daide_bytes: The bytes to use to build the clause
            :param on_error: The action to take when an error is encountered ('raise', 'warn', 'ignore')
            :return: The remaining (unparsed) bytes
        """
        turn_group_bytes, remaining_bytes = break_next_group(daide_bytes)

        # Can't find the order
        if not turn_group_bytes:
            self.error(on_error, 'Unable to find a set of parentheses to extract the turn clause.')
            return daide_bytes

        self._bytes = turn_group_bytes

        turn_group_bytes = strip_parentheses(turn_group_bytes)
        season, turn_group_bytes = parse_bytes(SingleToken, turn_group_bytes, on_error=on_error)
        year, turn_group_bytes = parse_bytes(Number, turn_group_bytes, on_error=on_error)

        if turn_group_bytes:
            self.error(on_error, '{} bytes remaining. Turn is malformed'.format(len(turn_group_bytes)))
            return daide_bytes

        season_alias = self._alias_from_bytes.get(str(season), str(season))
        self._str = ''.join([season_alias[0], str(year), season_alias[-1]])
        return remaining_bytes

class UnitType(SingleToken):
    """ Each clause is an season token
        Syntax: AMY
    """
    _alias_from_bytes = {'AMY': 'A',
                         'FLT': 'F'}

    def from_bytes(self, daide_bytes, on_error='raise'):
        """ Builds the clause from a byte array
            :param daide_bytes: The bytes to use to build the clause
            :param on_error: The action to take when an error is encountered ('raise', 'warn', 'ignore')
            :return: The remaining (unparsed) bytes
        """
        remaining_bytes = super(UnitType, self).from_bytes(daide_bytes, on_error)
        self._str = self._alias_from_bytes.get(self._str, self._str)
        return remaining_bytes

class Unit(AbstractClause):
    """ Each clause is an army or fleet
        Syntax: (ITA AMY TUN)
    """
    def __init__(self):
        """ Constructor """
        super(Unit, self).__init__()
        self._bytes = b''
        self._str = ''
        self._power_name = None

    @property
    def power_name(self):
        """ The power name """
        return self._power_name

    def __bytes__(self):
        """ Define the DAIDE bytes representation """
        return self._bytes

    def __str__(self):
        """ Return the Diplomacy str """
        return self._str

    def from_bytes(self, daide_bytes, on_error='raise'):
        """ Builds the clause from a byte array
            :param daide_bytes: The bytes to use to build the clause
            :param on_error: The action to take when an error is encountered ('raise', 'warn', 'ignore')
            :return: The remaining (unparsed) bytes
        """
        unit_group_bytes, remaining_bytes = break_next_group(daide_bytes)

        # Can't find the order
        if not unit_group_bytes:
            self.error(on_error, 'Unable to find a set of parentheses to extract the order clause.')
            return daide_bytes

        # Extract its content
        self._bytes = unit_group_bytes

        unit_group_bytes = strip_parentheses(unit_group_bytes)
        power, unit_group_bytes = parse_bytes(Power, unit_group_bytes, on_error=on_error)
        unit_type, unit_group_bytes = parse_bytes(UnitType, unit_group_bytes, on_error=on_error)
        province, unit_group_bytes = parse_bytes(Province, unit_group_bytes, on_error=on_error)

        if unit_group_bytes:
            self.error(on_error, '{} bytes remaining. Order is malformed'.format(len(unit_group_bytes)))
            return daide_bytes

        self._power_name = str(power)
        self._str = ' '.join([str(unit_type), str(province)])
        return remaining_bytes

class OrderType(SingleToken):
    """ Each clause is an order token
        Syntax: SUB
    """
    _alias_from_bytes = {'HLD': 'H',
                         'MTO': '-',
                         'SUP': 'S',
                         'CVY': 'C',
                         'CTO': '-',
                         'VIA': 'VIA',
                         'RTO': 'R',
                         'DSB': 'D',
                         'BLD': 'B',
                         'REM': 'D',
                         'WVE': 'WAIVE'}
    _alias_from_string = {'H': 'HLD',
                          '-': 'MTO',
                          'S': 'SUP',
                          'C': 'CVY',
                          'VIA': 'VIA',
                          'R': 'RTO',
                          'D': 'REM',
                          'B': 'BLD',
                          'WAIVE': 'WVE'}

    def from_bytes(self, daide_bytes, on_error='raise'):
        """ Builds the clause from a byte array
            :param daide_bytes: The bytes to use to build the clause
            :param on_error: The action to take when an error is encountered ('raise', 'warn', 'ignore')
            :return: The remaining (unparsed) bytes
        """
        remaining_bytes = super(OrderType, self).from_bytes(daide_bytes, on_error)
        self._str = self._alias_from_bytes.get(self._str, self._str)
        return remaining_bytes

class Order(AbstractClause):
    """ Each clause is an order
        Syntax: ((power unit_type location) order_type province)
    """
    def __init__(self):
        """ Constructor """
        super(Order, self).__init__()
        self._bytes = b''
        self._str = ''
        self._power_name = None

    @property
    def power_name(self):
        """ The power name """
        return self._power_name

    def __bytes__(self):
        """ Define the DAIDE bytes representation """
        return self._bytes

    def __str__(self):
        """ Return the Diplomacy str """
        return self._str

    def from_bytes(self, daide_bytes, on_error='raise'):
        """ Builds the clause from a byte array
            :param daide_bytes: The bytes to use to build the clause
            :param on_error: The action to take when an error is encountered ('raise', 'warn', 'ignore')
            :return: The remaining (unparsed) bytes
        """
        order_group_bytes, remaining_bytes = break_next_group(daide_bytes)

        # Can't find the order
        if not order_group_bytes:
            self.error(on_error, 'Unable to find a set of parentheses to extract the order clause.')
            return daide_bytes

        # Extract its content
        self._bytes = order_group_bytes

        # Parsing the unit group (or just the power)
        order_group_bytes = strip_parentheses(order_group_bytes)
        unit, order_group_bytes = parse_bytes(Unit, order_group_bytes, on_error='ignore')
        power = None
        if not unit:
            power, order_group_bytes = parse_bytes(Power, order_group_bytes, on_error='ignore')

        order_type, order_group_bytes = parse_bytes(OrderType, order_group_bytes, on_error=on_error)
        order_type_str = str(order_type)

        if order_type_str == 'WAIVE':
            str_buffer = [order_type_str]

        elif order_type_str:
            # Hold, Disband
            str_buffer = [str(unit), order_type_str]

            # Move order
            if order_type_str == '-':
                province, order_group_bytes = parse_bytes(Province, order_group_bytes, on_error=on_error)
                str_buffer += [str(province)]
                second_order_type, order_group_bytes = parse_bytes(OrderType, order_group_bytes, on_error='ignore')
                if str(second_order_type) == 'VIA':
                    str_buffer += [str(second_order_type)]
                    province_list, order_group_bytes = break_next_group(order_group_bytes)
                    del province_list

            # Support
            elif order_type_str == 'S':
                other_unit, order_group_bytes = parse_bytes(Unit, order_group_bytes, on_error=on_error)
                str_buffer += [str(other_unit)]
                second_order_type, order_group_bytes = parse_bytes(OrderType, order_group_bytes, on_error='ignore')
                if str(second_order_type) == '-':
                    province, order_group_bytes = parse_bytes(Province, order_group_bytes, on_error=on_error)
                    str_buffer += [str(second_order_type), str(province)]

            # Convoy
            elif order_type_str == 'C':
                other_unit, order_group_bytes = parse_bytes(Unit, order_group_bytes, on_error=on_error)
                second_order_type, order_group_bytes = parse_bytes(OrderType, order_group_bytes, on_error=on_error)
                province, order_group_bytes = parse_bytes(Province, order_group_bytes, on_error=on_error)
                str_buffer += [str(other_unit), str(second_order_type), str(province)]

            # Retreat
            elif order_type_str == 'R':
                province, order_group_bytes = parse_bytes(Province, order_group_bytes, on_error=on_error)
                str_buffer += [str(province)]

        else:
            self.error(on_error, 'Unable to find a unit, a power or an order to build the order clause')
            return daide_bytes

        if order_group_bytes:
            self.error(on_error, '{} bytes remaining. Order is malformed'.format(len(order_group_bytes)))
            return daide_bytes

        self._power_name = str(power) if power else unit.power_name
        self._str = ' '.join(str_buffer)
        return remaining_bytes
