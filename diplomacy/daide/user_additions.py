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

# ===================
# Daide user addition
# ===================

from diplomacy.utils import parsing, strings
from diplomacy.utils.jsonable import Jsonable

class UserAdditions(Jsonable):
    """ DAIDE user additions. """
    __slots__ = ['client_name', 'client_version', 'passcode']
    model = {
        strings.CLIENT_NAME: str,
        strings.CLIENT_VERSION: str,
        strings.PASSCODE: parsing.OptionalValueType(int)
    }

    def __init__(self, **kwargs):
        self.client_name = ''
        self.client_version = ''
        self.passcode = 0
        super(UserAdditions, self).__init__(**kwargs)
