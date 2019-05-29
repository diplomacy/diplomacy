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

class SubjectSplit():
    def __init__(self, length):
        self._in_str = None
        self._parts = [None] * length
        self._last_index = 0

    def __len__(self):
        return self._last_index

    @property
    def in_str(self):
        return self._in_str

    @property
    def parts(self):
        return self._parts[:self._last_index]

    def join(self):
        return ' '.join(str(self._parts[:self._last_index]))

class OrderSplit(SubjectSplit):
    def __init__(self):
        super(OrderSplit, self).__init__(6)

        self._unit_index = None
        self._command_index = None
        self._additional_unit_index = None
        self._additional_command_index = None
        self._province_index = None
        self._suffix_index = None

    @property
    def unit(self):
        return self._parts[self._unit_index] if self._unit_index is not None else None

    @unit.setter
    def unit(self, value):
        if self._unit_index is None:
            self._unit_index = self._last_index
            self._last_index += 1
        self._parts[self._unit_index] = value

    @property
    def command(self):
        return self._parts[self._command_index] if self._command_index is not None else None

    @command.setter
    def command(self, value):
        if self._command_index is None:
            self._command_index = self._last_index
            self._last_index += 1
        self._parts[self._command_index] = value

    @property
    def additional_unit(self):
        return self._parts[self._additional_unit_index] if self._additional_unit_index is not None else None

    @additional_unit.setter
    def additional_unit(self, value):
        if self._additional_unit_index is None:
            self._additional_unit_index = self._last_index
            self._last_index += 1
        self._parts[self._additional_unit_index] = value

    @property
    def additional_command(self):
        return self._parts[self._additional_command_index] if self._additional_command_index is not None else None

    @additional_command.setter
    def additional_command(self, value):
        if self._additional_command_index is None:
            self._additional_command_index = self._last_index
            self._last_index += 1
        self._parts[self._additional_command_index] = value

    @property
    def province(self):
        return self._parts[self._province_index] if self._province_index is not None else None

    @province.setter
    def province(self, value):
        if self._province_index is None:
            self._province_index = self._last_index
            self._last_index += 1
        self._parts[self._province_index] = value

    @property
    def suffix(self):
        return self._parts[self._suffix_index] if self._suffix_index is not None else None

    @suffix.setter
    def suffix(self, value):
        if self._suffix_index is None:
            self._suffix_index = self._last_index
            self._last_index += 1
        self._parts[self._suffix_index] = value

    @staticmethod
    def split(string):
        order = OrderSplit()
        order._in_str = string

        words = string.strip().split() if isinstance(string, str) else string

        # [WAIVE]
        if len(words) == 1:
            order.command = words.pop()
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
            order.unit = ' '.join([words.pop(0) for i in range(2)])
            order.command = words.pop(0)

            # [A, IRI, -, MAO]
            # [A, IRI, R, MAO]
            if order.command in '-R':
                order.province = words.pop()
            # [A, WAL, S, F, LON]
            # [A, WAL, S, F, MAO, -, IRI]
            # [F, NWG, C, A, NWY, -, EDI]
            elif order.command in 'SC':
                order.additional_unit = ' '.join([words.pop(0) for i in range(2)])
                # [A, WAL, S, F, MAO, -, IRI]
                # [F, NWG, C, A, NWY, -, EDI]
                if words:
                    order.additional_command = words.pop(0)
                    order.province = words.pop(0)

            # [A, IRI, -, MAO, VIA]
            if words and words[-1] == 'VIA':
                order.suffix = words.pop()

        return order

class PhaseSplit(SubjectSplit):
    def __init__(self):
        super(PhaseSplit, self).__init__(3)

        self._season_index = None
        self._year_index = None
        self._type_index = None

    @property
    def season(self):
        return self._parts[self._season_index] if self._season_index is not None else None

    @season.setter
    def season(self, value):
        if self._season_index is None:
            self._season_index = self._last_index
            self._last_index += 1
        self._parts[self._season_index] = value

    @property
    def year(self):
        return self._parts[self._year_index] if self._year_index is not None else None

    @year.setter
    def year(self, value):
        if self._year_index is None:
            self._year_index = self._last_index
            self._last_index += 1
        self._parts[self._year_index] = value

    @property
    def type(self):
        return self._parts[self._type_index] if self._type_index is not None else None

    @type.setter
    def type(self, value):
        if self._type_index is None:
            self._type_index = self._last_index
            self._last_index += 1
        self._parts[self._type_index] = value

    @staticmethod
    def split(string):
        phase = PhaseSplit()
        phase._in_str = string

        phase.season = string[0]
        phase.year = int(string[1:-1])
        phase.type = string[-1]

        return phase
