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
""" SubjectSplit
    - Contains utils to retrieve splitted subjects fields
"""

from abc import ABCMeta, abstractmethod

class SubjectSplit(metaclass=ABCMeta):
    """ Represents a splitted subject """
    def __init__(self, string, length):
        """ Constructor
            :param string: the string to split
            :param length: the maximum length of the split
        """
        self._in_str = string if isinstance(string, str) else ' '.join(string)
        self._parts = [None] * length
        self._last_index = 0

        self._split()

    def __len__(self):
        """ Define the length of the split """
        return self._last_index

    @property
    def in_str(self):
        """ Return the input string used to build the split """
        return self._in_str

    @property
    def parts(self):
        """ Return the array of the parts after split """
        return self._parts[:self._last_index]

    def join(self):
        """ Return the joined parts """
        return ' '.join(str(self._parts[:self._last_index]))

    @abstractmethod
    def _split(self):
        """ Build the subject split using it's _in_str """
        raise NotImplementedError()

class OrderSplit(SubjectSplit):
    """ Represents a splitted order """
    def __init__(self, string):
        """ Constructor
            :param string: the string to split
        """
        self._unit_index = None
        self._command_index = None
        self._additional_unit_index = None
        self._additional_command_index = None
        self._province_index = None
        self._suffix_index = None

        super(OrderSplit, self).__init__(string, 6)

    @property
    def unit(self):
        """ Return the unit of the order """
        return self._parts[self._unit_index] if self._unit_index is not None else None

    @unit.setter
    def unit(self, value):
        """ Set the unit of the order and define the index of the part if not already set """
        if self._unit_index is None:
            self._unit_index = self._last_index
            self._last_index += 1
        self._parts[self._unit_index] = value

    @property
    def command(self):
        """ Return the command of the order """
        return self._parts[self._command_index] if self._command_index is not None else None

    @command.setter
    def command(self, value):
        """ Set the command of the order and define the index of the part if not already set """
        if self._command_index is None:
            self._command_index = self._last_index
            self._last_index += 1
        self._parts[self._command_index] = value

    @property
    def additional_unit(self):
        """ Return the additional unit of the order """
        return self._parts[self._additional_unit_index] if self._additional_unit_index is not None else None

    @additional_unit.setter
    def additional_unit(self, value):
        """ Set the additional unit of the order and define the index of the part if not already set """
        if self._additional_unit_index is None:
            self._additional_unit_index = self._last_index
            self._last_index += 1
        self._parts[self._additional_unit_index] = value

    @property
    def additional_command(self):
        """ Return the additional command of the order """
        return self._parts[self._additional_command_index] if self._additional_command_index is not None else None

    @additional_command.setter
    def additional_command(self, value):
        """ Set the additional command of the order and define the index of the part if not already set """
        if self._additional_command_index is None:
            self._additional_command_index = self._last_index
            self._last_index += 1
        self._parts[self._additional_command_index] = value

    @property
    def province(self):
        """ Return the province of the order """
        return self._parts[self._province_index] if self._province_index is not None else None

    @province.setter
    def province(self, value):
        """ Set the province of the order and define the index of the part if not already set """
        if self._province_index is None:
            self._province_index = self._last_index
            self._last_index += 1
        self._parts[self._province_index] = value

    @property
    def suffix(self):
        """ Return the suffix keyword of the order """
        return self._parts[self._suffix_index] if self._suffix_index is not None else None

    @suffix.setter
    def suffix(self, value):
        """ Set the suffix of the order and define the index of the part if not already set """
        if self._suffix_index is None:
            self._suffix_index = self._last_index
            self._last_index += 1
        self._parts[self._suffix_index] = value

    def _split(self):
        """ Build the subject split using it's _in_str """
        words = self._in_str.strip().split() if isinstance(self._in_str, str) else self._in_str

        # [WAIVE]
        if len(words) == 1:
            self.command = words.pop()
        # [A, LON, H]
        # [F, IRI, -, MAO]
        # [A, IRI, -, MAO, VIA]
        # [A, WAL, S, F,   LON]
        # [A, WAL, S, F,   MAO, -, IRI]
        # [F, NWG, C, A,   NWY, -, EDI]
        # [A, IRO, R, MAO]
        # [A, IRO, D]
        # [A, LON, B]
        # [F, LIV, B]
        else:
            self.unit = ' '.join([words.pop(0) for i in range(2)])
            self.command = words.pop(0)

            # [A, IRI, -, MAO]
            # [A, IRI, R, MAO]
            if self.command in '-R':
                self.province = words.pop()
            # [A, WAL, S, F, LON]
            # [A, WAL, S, F, MAO, -, IRI]
            # [F, NWG, C, A, NWY, -, EDI]
            elif self.command in 'SC':
                self.additional_unit = ' '.join([words.pop(0) for i in range(2)])
                # [A, WAL, S, F, MAO, -, IRI]
                # [F, NWG, C, A, NWY, -, EDI]
                if words:
                    self.additional_command = words.pop(0)
                    self.province = words.pop(0)

            # [A, IRI, -, MAO, VIA]
            if words and words[-1] == 'VIA':
                self.suffix = words.pop()

class PhaseSplit(SubjectSplit):
    """ Represents a splitted phase """
    def __init__(self, string):
        """ Constructor
            :param string: the string to split
        """
        self._season_index = None
        self._year_index = None
        self._type_index = None

        super(PhaseSplit, self).__init__(string, 3)

    @property
    def season(self):
        """ Return the season of the phase """
        return self._parts[self._season_index] if self._season_index is not None else None

    @season.setter
    def season(self, value):
        """ Set the season of the phase and define the index of the part if not already set """
        if self._season_index is None:
            self._season_index = self._last_index
            self._last_index += 1
        self._parts[self._season_index] = value

    @property
    def year(self):
        """ Return the year of the phase """
        return self._parts[self._year_index] if self._year_index is not None else None

    @year.setter
    def year(self, value):
        """ Set the year of the phase and define the index of the part if not already set """
        if self._year_index is None:
            self._year_index = self._last_index
            self._last_index += 1
        self._parts[self._year_index] = value

    @property
    def type(self):
        """ Return the type of the phase """
        return self._parts[self._type_index] if self._type_index is not None else None

    @type.setter
    def type(self, value):
        """ Set the type of the phase and define the index of the part if not already set """
        if self._type_index is None:
            self._type_index = self._last_index
            self._last_index += 1
        self._parts[self._type_index] = value

    def _split(self):
        """ Build the subject split using it's _in_str """
        self.season = self._in_str[0]
        self.year = int(self._in_str[1:-1])
        self.type = self._in_str[-1]
