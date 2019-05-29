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
""" DAIDE Notifications - Contains a list of responses sent by the server to the client """
import diplomacy.daide as daide
import diplomacy.daide.clauses
from diplomacy.daide.clauses import add_parentheses, strip_parentheses, parse_string
import diplomacy.daide.tokens
from diplomacy.daide.tokens import Token
from diplomacy.daide.utils import bytes_to_str, str_to_bytes
from diplomacy import Map

class DaideNotification():
    """ Represents a DAIDE response. """
    def __init__(self, **kwargs):
        """ Constructor """
        self._bytes = b''
        self._str = ''

    def __bytes__(self):
        """ Returning the bytes representation of the response """
        return self._bytes

    def __str__(self):
        """ Returning the string representation of the response """
        return bytes_to_str(self._bytes)

class MapNameNotification(DaideNotification):
    """ Represents a MAP DAIDE response. Sends the name of the current map to the client.
        Syntax:
            MAP ('name')
    """
    def __init__(self, map_name, **kwargs):
        """ Builds the response
            :param map_name: String. The name of the current map.
        """
        super(MapNameNotification, self).__init__(**kwargs)
        self._bytes = bytes(daide.tokens.MAP) \
                      + bytes(parse_string(daide.clauses.String, map_name))

class HelloNotification(DaideNotification):
    """ Represents a HLO DAIDE response. Sends the power to be played by the client with the passcode to rejoin the
        game and the details of the game.
        Syntax:
            HLO (power) (passcode) (variant) (variant) ...
        Variant syntax:
            LVL n           # Level of the syntax accepted
            MTL seconds     # Movement time limit
            RTL seconds     # Retreat time limit
            BTL seconds     # Build time limit
            DSD             # Disables the time limit when a client disconects
            AOA             # Any orders accepted
        LVL 10:
        Variant syntax:
            PDA             # Accept partial draws
            NPR             # No press during retreat phases
            NPB             # No press during build phases
            PTL seconds     # Press time limit
    """
    def __init__(self, power_name, passcode, level, deadline, rules, **kwargs):
        """ Builds the response
            :param power_name: The name of the power being played.
            :param passcode: Integer. A passcode to rejoin the game.
            :param level: Integer. The daide syntax level of the game
            :param deadline: Integer. The number of seconds per turn (0 to disable)
            :param rules: The list of game rules.
        """
        super(HelloNotification, self).__init__(**kwargs)
        power = parse_string(daide.clauses.Power, power_name)
        passcode = Token(from_int=passcode)

        if 'NO_PRESS' in rules:
            level = 0
        variants = add_parentheses(bytes(daide.tokens.LVL) + bytes(Token(from_int=level)))

        if deadline > 0:
            variants += add_parentheses(bytes(daide.tokens.MTL) + bytes(Token(from_int=deadline)))
            variants += add_parentheses(bytes(daide.tokens.RTL) + bytes(Token(from_int=deadline)))
            variants += add_parentheses(bytes(daide.tokens.BTL) + bytes(Token(from_int=deadline)))

        if 'NO_CHECK' in rules:
            variants += add_parentheses(bytes(daide.tokens.AOA))

        self._bytes = bytes(daide.tokens.HLO) \
                      + add_parentheses(bytes(power)) \
                      + add_parentheses(bytes(passcode)) \
                      + add_parentheses(bytes(variants))

class SupplyCenterNotification(DaideNotification):
    """ Represents a SCO DAIDE response. Sends the current supply centre ownership.
        Syntax:
            SCO (power centre centre ...) (power centre centre ...) ...
    """
    def __init__(self, powers_centers, map_name, **kwargs):
        """ Builds the response
            :param powers: A list of `diplomacy.engine.power.Power` objects
            :param map_name: The name of the map
        """
        super(SupplyCenterNotification, self).__init__(**kwargs)
        remaining_scs = Map(map_name).scs[:]
        all_powers_bytes = []

        # Parsing each power
        for power_name, centers in powers_centers.items():
            power_clause = parse_string(daide.clauses.Power, power_name)
            power_bytes = bytes(power_clause)

            for center in centers:
                sc_clause = parse_string(daide.clauses.Province, center)
                power_bytes += bytes(sc_clause)
                remaining_scs.remove(center)

            all_powers_bytes += [power_bytes]

        # Parsing unowned center
        uno_token = daide.tokens.UNO
        power_bytes = bytes(uno_token)

        for center in remaining_scs:
            sc_clause = parse_string(daide.clauses.Province, center)
            power_bytes += bytes(sc_clause)

        all_powers_bytes += [power_bytes]

        # Storing full response
        self._bytes = bytes(daide.tokens.SCO) \
                      + b''.join([add_parentheses(power_bytes) for power_bytes in all_powers_bytes])

class CurrentPositionNotification(DaideNotification):
    """ Represents a NOW DAIDE response. Sends the current turn, and the current unit positions.
        Syntax:
            NOW (turn) (unit) (unit) ...
        Unit syntax:
            power unit_type province
            power unit_type province MRT (province province ...)
    """
    def __init__(self, phase_name, powers_units, powers_retreats, **kwargs):
        """ Builds the response
            :param phase_name: The name of the current phase (e.g. 'S1901M')
            :param powers: A list of `diplomacy.engine.power.Power` objects
        """
        super(CurrentPositionNotification, self).__init__(**kwargs)
        units_bytes_buffer = []

        # Turn
        turn_clause = parse_string(daide.clauses.Turn, phase_name)

        # Units
        for power_name, units in powers_units.items():
            # Regular units
            for unit in units:
                unit_clause = parse_string(daide.clauses.Unit, '%s %s' % (power_name, unit))
                units_bytes_buffer += [bytes(unit_clause)]

            # Dislodged units
            for unit, retreat_provinces in powers_retreats[power_name].items():
                unit_clause = parse_string(daide.clauses.Unit, '%s %s' % (power_name, unit))
                retreat_clauses = [parse_string(daide.clauses.Province, province)
                                   for province in retreat_provinces]
                units_bytes_buffer += [add_parentheses(strip_parentheses(bytes(unit_clause))
                                                       + bytes(daide.tokens.MRT)
                                                       + add_parentheses(b''.join([bytes(province)
                                                                                   for province in retreat_clauses])))]

        # Storing full response
        self._bytes = bytes(daide.tokens.NOW) + bytes(turn_clause) + b''.join(units_bytes_buffer)

class MissingOrdersNotification(DaideNotification):
    """ Represents a MIS DAIDE response. Sends the list of unit for which an order is missing or indication about
        required disbands or builds.
        Syntax:
            MIS (unit) (unit) ...
            MIS (unit MRT (province province ...)) (unit MRT (province province ...)) ...
            MIS (number)
    """
    def __init__(self, phase_name, power, **kwargs):
        """ Builds the response
            :param phase_name: The name of the current phase (e.g. 'S1901M')
            :param power: The power to check for missing orders
            :type power: diplomacy.engine.power.Power
        """
        super(MissingOrdersNotification, self).__init__(**kwargs)
        assert phase_name[-1] in 'MRA', 'Invalid phase "%s"' & phase_name
        {'M': self._build_movement_phase,
         'R': self._build_retreat_phase,
         'A': self._build_adjustment_phase}[phase_name[-1]](power)

    def _build_movement_phase(self, power):
        """ Builds the missing orders response for a movement phase """
        units_with_no_order = [unit for unit in power.units]

        # Removing units for which we have orders
        for key, value in power.orders.items():
            unit = key                              # Regular game {e.g. 'A PAR': '- BUR')
            if key[0] in 'RIO':                     # No-check game (key is INVALID, ORDER x, REORDER x)
                unit = ' '.join(value.split()[:2])
            if unit in units_with_no_order:
                units_with_no_order.remove(unit)

        # Storing full response
        self._bytes = bytes(daide.tokens.MIS) + b''.join([bytes(parse_string(daide.clauses.Unit, '%s %s' % (power.name, unit)))
                                                          for unit in units_with_no_order])

    def _build_retreat_phase(self, power):
        """ Builds the missing orders response for a retreat phase """
        units_bytes_buffer = []

        units_with_no_order = {unit: retreat_provinces for unit, retreat_provinces in power.retreats.items()}

        # Removing units for which we have orders
        for key, value in power.orders.items():
            unit = key                              # Regular game {e.g. 'A PAR': '- BUR')
            if key[0] in 'RIO':                     # No-check game (key is INVALID, ORDER x, REORDER x)
                unit = ' '.join(value.split()[:2])
            if unit in units_with_no_order:
                units_with_no_order.remove(unit)

        for unit, retreat_provinces in units_with_no_order.items():
            unit_clause = parse_string(daide.clauses.Unit, '%s %s' % (power.name, unit))
            retreat_clauses = [parse_string(daide.clauses.Province, province)
                               for province in retreat_provinces]
            units_bytes_buffer += [add_parentheses(strip_parentheses(bytes(unit_clause))
                                                   + bytes(daide.tokens.MRT)
                                                   + add_parentheses(b''.join([bytes(province)
                                                                               for province in retreat_clauses])))]

        self._bytes = bytes(daide.tokens.MIS) + b''.join(units_bytes_buffer)

    def _build_adjustment_phase(self, power):
        """ Builds the missing orders response for a build phase """
        disbands_status = len(power.units) - len(power.centers)

        if disbands_status < 0:
            available_homes = power.homes[:]

            # Removing centers for which it's impossible to build
            for unit in [unit.split() for unit in power.units]:
                province = unit[1]
                if province in available_homes:
                    available_homes.remove(province)

            disbands_status = max(-len(available_homes), disbands_status)

        self._bytes += bytes(daide.tokens.MIS) + add_parentheses(bytes(daide.tokens.Token(from_int=disbands_status)))

class OrderResultNotification(DaideNotification):
    """ Represents a ORD DAIDE response. Sends the result of an order after the turn has been processed.
        Syntax:
            ORD (turn) (order) (result)
            ORD (turn) (order) (result RET)
        Result syntax:
            SUC         # Order succeeded (can apply to any order).
            BNC         # Move bounced (only for MTO, CTO or RTO orders).
            CUT         # Support cut (only for SUP orders).
            DSR         # Move via convoy failed due to dislodged convoying fleet (only for CTO orders).
            NSO         # No such order (only for SUP, CVY or CTO orders).
            RET         # Unit was dislodged and must retreat.
    """
    def __init__(self, phase_name, order_bytes, results, **kwargs):
        """ Builds the response
            :param phase_name: The name of the current phase (e.g. 'S1901M')
            :param order_bytes: The bytes received for the order
            :param results: An array containing the error codes.
        """
        super(OrderResultNotification, self).__init__(**kwargs)
        turn_clause = parse_string(daide.clauses.Turn, phase_name)
        result_clause = None
        if not results or 0 in results:         # Order success response
            result_clause = daide.tokens.SUC
        else:                                   # Generic order failure response
            result_clause = daide.tokens.NSO

        self._bytes = bytes(daide.tokens.ORD) + bytes(turn_clause) + add_parentheses(order_bytes) + \
                      add_parentheses(bytes(result_clause))

class TimeToDeadlineNotification(DaideNotification):
    """ Represents a TME DAIDE response. Sends the time to the next deadline.
        Syntax:
            TME (seconds)
    """
    def __init__(self, seconds, **kwargs):
        """ Builds the response
            :param seconds: Integer. The number of seconds before deadline
        """
        super(TimeToDeadlineNotification, self).__init__(**kwargs)
        self._bytes = bytes(daide.tokens.TME) + add_parentheses(bytes(daide.tokens.Token(from_int=seconds)))

class PowerInCivilDisorderNotification(DaideNotification):
    """ Represents a CCD DAIDE response. Sends the name of the power in civil disorder.
        Syntax:
            CCD (power)
    """
    def __init__(self, power_name, **kwargs):
        """ Builds the response
            :param power_name: The name of the power being played.
        """
        super(PowerInCivilDisorderNotification, self).__init__(**kwargs)
        power = parse_string(daide.clauses.Power, power_name)
        self._bytes = bytes(daide.tokens.CCD) + add_parentheses(bytes(power))

class PowerIsEliminatedNotification(DaideNotification):
    """ Represents a OUT DAIDE response. Sends the name of the power eliminated.
        Syntax:
            OUT (power)
    """
    def __init__(self, power_name, **kwargs):
        """ Builds the response
            :param power_name: The name of the power being played.
        """
        super(PowerIsEliminatedNotification, self).__init__(**kwargs)
        power = parse_string(daide.clauses.Power, power_name)
        self._bytes = bytes(daide.tokens.OUT) + add_parentheses(bytes(power))

class DrawNotification(DaideNotification):
    """ Represents a DRW DAIDE response. Indicates that the game has ended due to a draw
        Syntax:
            DRW
    """
    def __init__(self, **kwargs):
        """ Builds the response
        """
        super(DrawNotification, self).__init__(**kwargs)
        self._bytes = bytes(daide.tokens.DRW)

class MessageFromNotification(DaideNotification):
    """ Represents a FRM DAIDE response. Indicates that the game has ended due to a draw
        Syntax:
            FRM (power) (power power ...) (press_message)
            FRM (power) (power power ...) (reply)
    """
    def __init__(self, from_power_name, to_power_names, message, **kwargs):
        """ Builds the response
        """
        super(MessageFromNotification, self).__init__(**kwargs)

        from_power_clause = bytes(parse_string(daide.clauses.Power, from_power_name))

        to_powers_clause = b''.join([bytes(parse_string(daide.clauses.Power, power_name)) for power_name in to_power_names])

        message_clause = str_to_bytes(message)

        self._bytes = bytes(daide.tokens.FRM) \
                      + b''.join([add_parentheses(clause)
                                  for clause in [from_power_clause, to_powers_clause, message_clause]])

class SoloNotification(DaideNotification):
    """ Represents a SLO DAIDE response. Indicates that the game has ended due to a solo by the specified power
        Syntax:
            SLO (power)
    """
    def __init__(self, power_name, **kwargs):
        """ Builds the response
            :param power_name: The name of the power being solo.
        """
        super(SoloNotification, self).__init__(**kwargs)
        power = parse_string(daide.clauses.Power, power_name)
        self._bytes = bytes(daide.tokens.SLO) + add_parentheses(bytes(power))

# TODO: implement
class SummaryNotification(DaideNotification):
    """ Represents a SMR DAIDE response. Sends the summary for each power at the end of the game
        Syntax:
            SMR (turn) (power_summary) ...
        power_summary syntax:
            power ('name') ('version') number_of_centres
            power ('name') ('version') number_of_centres year_of_elimination
    """
    def __init__(self, phase_name, powers, **kwargs):
        """ Builds the response
        """
        raise NotImplementedError

class TurnOffNotification(DaideNotification):
    """ Represents an OFF DAIDE response. Requests a client to exit
        Syntax:
            OFF
    """
    def __init__(self, **kwargs):
        """ Builds the response
        """
        super(TurnOffNotification, self).__init__(**kwargs)
        self._bytes = bytes(daide.tokens.OFF)

MAP = MapNameNotification
HLO = HelloNotification
SCO = SupplyCenterNotification
NOW = CurrentPositionNotification
MIS = MissingOrdersNotification
ORD = OrderResultNotification
TME = TimeToDeadlineNotification
CCD = PowerInCivilDisorderNotification
OUT = PowerIsEliminatedNotification
DRW = DrawNotification
FRM = MessageFromNotification
SLO = SoloNotification
SMR = SummaryNotification
OFF = TurnOffNotification
