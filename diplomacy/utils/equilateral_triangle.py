class EquilateralTriangle:
    """ Helper class that represent an equilateral triangle.
        Used to compute intersection of a line with a side of convoy symbol, which is an equilateral triangle.
    """
    __slots__ = ('x_A', 'y_A', 'x_B', 'y_B', 'x_C', 'y_C', 'x_O', 'y_O', 'h',
                 'line_AB_a', 'line_AB_b', 'line_AC_a', 'line_AC_b')

    def __init__(self, x_top, y_top, x_right, y_right, x_left, y_left):
        # type: (float, float, float, float, float, float) -> None
        assert y_left == y_right > y_top
        assert x_left < x_top < x_right
        self.x_A = x_top
        self.y_A = y_top
        self.x_B = x_right
        self.y_B = y_right
        self.x_C = x_left
        self.y_C = y_left
        self.h = self.y_B - self.y_A
        self.x_O = self.x_A
        self.y_O = self.y_A + 2 * self.h / 3
        self.line_AB_a = (self.y_B - self.y_A) / (self.x_B - self.x_A)
        self.line_AB_b = self.y_B - self.x_B * self.line_AB_a
        self.line_AC_a = (self.y_C - self.y_A) / (self.x_C - self.x_A)
        self.line_AC_b = self.y_C - self.x_C * self.line_AC_a

    def __line_OM(self, x_M, y_M):
        a = (y_M - self.y_O) / (x_M - self.x_O)
        b = y_M - a * x_M
        return a, b

    def __intersection_with_AB(self, x_M, y_M):
        a, b = self.line_AB_a, self.line_AB_b
        u, v = self.__line_OM(x_M, y_M)
        assert a != u
        x = (v - b) / (a - u)
        y = a * x + b
        if self.x_A <= x <= self.x_B and self.y_A <= y <= self.y_B:
            return x, y
        return None, None

    def __intersection_with_AC(self, x_M, y_M):
        a, b = self.line_AC_a, self.line_AC_b
        u, v = self.__line_OM(x_M, y_M)
        x = (v - b) / (a - u)
        y = a * x + b
        if self.x_C <= x <= self.x_A and self.y_A <= y <= self.y_C:
            return x, y
        return None, None

    def __intersection_with_BC(self, x_M, y_M):
        a, b = self.__line_OM(x_M, y_M)
        y = self.y_C
        x = (y - b) / a
        if self.x_C <= x <= self.x_A:
            return x, y
        return None, None

    def intersection(self, x_M, y_M):
        # type: (float, float) -> (float, float)
        if self.x_O == x_M and self.y_O == y_M:
            return x_M, y_M
        if self.x_O == x_M:
            if y_M < self.y_O:
                return x_M, self.y_A
            else:
                # vertical line intersects BC
                return x_M, self.y_C
        elif self.y_O == y_M:
            if x_M < self.x_O:
                # horizontal line intersects AC
                a, b = self.line_AC_a, self.line_AC_b
            else:
                # horizontal line intersects AB
                a, b = self.line_AB_a, self.line_AB_b
            x = (y_M - b) / a
            return x, y_M
        else:
            # get nearest point in intersections with AB, AC, BC
            p1_x, p1_y = self.__intersection_with_AB(x_M, y_M)
            p2_x, p2_y = self.__intersection_with_AC(x_M, y_M)
            p3_x, p3_y = self.__intersection_with_BC(x_M, y_M)
            distances = []
            if p1_x is not None:
                d1 = ((p1_x - x_M) ** 2 + (p1_y - y_M) ** 2) ** 0.5
                distances.append((d1, p1_x, p1_y))
            if p2_x is not None:
                d2 = ((p2_x - x_M) ** 2 + (p2_y - y_M) ** 2) ** 0.5
                distances.append((d2, p2_x, p2_y))
            if p3_x is not None:
                d3 = ((p3_x - x_M) ** 2 + (p3_y - y_M) ** 2) ** 0.5
                distances.append((d3, p3_x, p3_y))
            assert distances
            distances.sort()
            return distances[0][1:]