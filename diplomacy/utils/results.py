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
""" Results
    - Contains the results labels and code used by the engine
"""
ORDER_RESULT_OFFSET = 10000

class Result():
    """ Represents a result """
    def __init__(self, code, message=None):
        """ Build a Result
            :param code: int code of the result
            :param message: humain readable string message associated to the result
        """
        if isinstance(code, str) or message is None:
            message = code
            code = None

        if code is None:
            splitted_message = message.split(':')
            code = int(splitted_message[0])
            message = ':'.join(splitted_message[1:])

        self._code = code
        self._message = message

    def __eq__(self, other):
        """ Define the equal """
        if isinstance(other, Result):
            return self._code == other.code

        return self._message == str(other)

    def __hash__(self):
        """ Define the hash """
        return hash(self._message)

    def __mod__(self, values):
        """ Define the modulus. Apply the modulus on the result's message """
        return Result(self._code, self._message % values)

    def __repr__(self):
        """ Define the string representation """
        return '{}:{}'.format(self._code, self._message)

    @property
    def code(self):
        """ Return the code of the result """
        return self._code

    @property
    def message(self):
        """ Return the message of the result """
        return self._message

    def format(self, *values):
        """ Format the message of the result """
        return Result(self._code, self._message.format(*values))

class OrderResult(Result):
    """ Represents an order result """
    def __init__(self, code, message):
        """ Build a Result
            :param code: int code of the result
            :param message: humain readable string message associated to the result
        """
        super(OrderResult, self).__init__(self.OFFSET+code, message)

    OFFSET = ORDER_RESULT_OFFSET

OK = Result(0, '')

ORDER_NO_CONVOY = OrderResult(0, 'no convoy')
ORDER_BOUNCE = OrderResult(1, 'bounce')
ORDER_VOID = OrderResult(2, 'void')
ORDER_CUT = OrderResult(3, 'cut')
ORDER_DISLODGED = OrderResult(4, 'dislodged')
ORDER_DISRUPTED = OrderResult(5, 'disrupted')
ORDER_DISBAND = OrderResult(6, 'disband')
