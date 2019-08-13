""" Helper class to compute intersection of a line (OM) with a side of an equilateral triangle,
    with O the barycenter of the equilateral triangle and M a point outside the triangle.
"""

class EquilateralTriangle:
    """ Helper class that represent an equilateral triangle.
        Used to compute intersection of a line with a side of convoy symbol, which is an equilateral triangle.
    """
    __slots__ = ('x_a', 'y_a', 'x_b', 'y_b', 'x_c', 'y_c', 'x_o', 'y_o', 'height',
                 'line_ab_a', 'line_ab_b', 'line_ac_a', 'line_ac_b')

    def __init__(self, x_top, y_top, x_right, y_right, x_left, y_left):
        # type: (float, float, float, float, float, float) -> None
        assert y_left == y_right > y_top
        assert x_left < x_top < x_right
        self.x_a = x_top
        self.y_a = y_top
        self.x_b = x_right
        self.y_b = y_right
        self.x_c = x_left
        self.y_c = y_left
        self.height = self.y_b - self.y_a
        self.x_o = self.x_a
        self.y_o = self.y_a + 2 * self.height / 3
        self.line_ab_a = (self.y_b - self.y_a) / (self.x_b - self.x_a)
        self.line_ab_b = self.y_b - self.x_b * self.line_ab_a
        self.line_ac_a = (self.y_c - self.y_a) / (self.x_c - self.x_a)
        self.line_ac_b = self.y_c - self.x_c * self.line_ac_a

    def __line_om(self, x_m, y_m):
        # pylint:disable=invalid-name
        a = (y_m - self.y_o) / (x_m - self.x_o)
        b = y_m - a * x_m
        return a, b

    def __intersection_with_ab(self, x_m, y_m):
        # pylint:disable=invalid-name
        a, b = self.line_ab_a, self.line_ab_b
        u, v = self.__line_om(x_m, y_m)
        assert a != u
        x = (v - b) / (a - u)
        y = a * x + b
        if self.x_a <= x <= self.x_b and self.y_a <= y <= self.y_b:
            return x, y
        return None, None

    def __intersection_with_ac(self, x_m, y_m):
        # pylint:disable=invalid-name
        a, b = self.line_ac_a, self.line_ac_b
        u, v = self.__line_om(x_m, y_m)
        x = (v - b) / (a - u)
        y = a * x + b
        if self.x_c <= x <= self.x_a and self.y_a <= y <= self.y_c:
            return x, y
        return None, None

    def __intersection_with_bc(self, x_m, y_m):
        # pylint:disable=invalid-name
        a, b = self.__line_om(x_m, y_m)
        y = self.y_c
        x = (y - b) / a
        if self.x_c <= x <= self.x_a:
            return x, y
        return None, None

    def intersection(self, x_m, y_m):
        # type: (float, float) -> (float, float)
        # pylint:disable=invalid-name
        """ Return coordinates of the intersection of (OM) with equilateral triangle,
            with M the point with coordinates (x_m, y_m). Only the intersection with
            the side of triangle near M is considered.
            :param x_m: x coordinate of M
            :param y_m: y coordinate of M
            :return: a couple (x, y) of floating values.
        """
        if self.x_o == x_m and self.y_o == y_m:
            return x_m, y_m
        if self.x_o == x_m:
            if y_m < self.y_o:
                return x_m, self.y_a
            # Otherwise, vertical line intersects BC
            return x_m, self.y_c
        if self.y_o == y_m:
            if x_m < self.x_o:
                # horizontal line intersects AC
                a, b = self.line_ac_a, self.line_ac_b
            else:
                # horizontal line intersects AB
                a, b = self.line_ab_a, self.line_ab_b
            x = (y_m - b) / a
            return x, y_m
        # Otherwise, get nearest point in intersections with AB, AC, BC
        p1_x, p1_y = self.__intersection_with_ab(x_m, y_m)
        p2_x, p2_y = self.__intersection_with_ac(x_m, y_m)
        p3_x, p3_y = self.__intersection_with_bc(x_m, y_m)
        distances = []
        if p1_x is not None:
            distance_1 = ((p1_x - x_m) ** 2 + (p1_y - y_m) ** 2) ** 0.5
            distances.append((distance_1, p1_x, p1_y))
        if p2_x is not None:
            distance_2 = ((p2_x - x_m) ** 2 + (p2_y - y_m) ** 2) ** 0.5
            distances.append((distance_2, p2_x, p2_y))
        if p3_x is not None:
            distance_3 = ((p3_x - x_m) ** 2 + (p3_y - y_m) ** 2) ** 0.5
            distances.append((distance_3, p3_x, p3_y))
        assert distances
        distances.sort()
        return distances[0][1:]
