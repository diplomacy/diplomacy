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
MESSAGE_TO_CODE = {}

ORDER_RESULT_OFFSET = 4000

class Result():
    def __init__(self, code, message=None):
        if message is None:
            message = code
            code = MESSAGE_TO_CODE[message]

        self._code = code
        self._message = message

    def __eq__(self, other):
        """ Define the equal """
        if isinstance(other, Result):
            return self._code == other.code

        return self._message == str(other)

    def __hash__(self):
        return hash(self._message)

    def __mod__(self, values):
        return Result(self._code, self._message % values)

    def __str__(self):
        return self._message

    def __repr__(self):
        return '{}:{}'.format(self._code, self._message)

    @property
    def code(self):
        return self._code

    @property
    def message(self):
        return self._message

    def format(self, *values):
        return Result(self._code, self._message.format(*values))

class OrderResult(Result):
    def __init__(self, code, message):
        super(OrderResult, self).__init__(self.OFFSET+code, message)

    OFFSET = ORDER_RESULT_OFFSET

def register_result(result_class, code, message):
    MESSAGE_TO_CODE[message] = code
    return result_class(code, message)

OK = register_result(Result, 0, '')

ORDER_NO_CONVOY = register_result(OrderResult, 0, 'no convoy')
ORDER_BOUNCE = register_result(OrderResult, 1, 'bounce')
ORDER_VOID = register_result(OrderResult, 2, 'void')
ORDER_CUT = register_result(OrderResult, 3, 'cut')
ORDER_DISLODGED = register_result(OrderResult, 4, 'dislodged')
ORDER_DISRUPTED = register_result(OrderResult, 5, 'disrupted')
ORDER_DISBAND = register_result(OrderResult, 6, 'disband')
