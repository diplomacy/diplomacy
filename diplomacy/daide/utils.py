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
import diplomacy.daide as daide
from diplomacy.daide.tokens import is_integer_token, Token

def str_to_bytes(daide_str):
    """ Converts a str into its bytes representation
        :param daide_str: A DAIDE string with tokens separated by spaces
        :return: The bytes representation of the string

        Note: Integers starts with a '#' character
    """
    buffer = []
    for word in daide_str.split(' '):
        if word == '':
            buffer.append(bytes(Token(from_str=' ')))
        elif word[0] == '#':
            buffer.append(bytes(Token(from_int=int(word[1:]))))
        else:
            buffer.append(bytes(Token(from_str=word)))
    return b''.join(buffer)
