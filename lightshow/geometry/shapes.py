from lightshow.core.types import *
from typing import List
import lightshow.core.utils as utils

class Sphere(Shape):

    def __init__(self, radius: float, origin: Point = Point(0, 0, 0)):
        super(Sphere, self).__init__()
        self._radius = radius
        self._origin = origin
        self._bounding_cube = Cube(Point(origin.x - radius,
                                         origin.y - radius,
                                         origin.z - radius),
                                   Point(origin.x + radius,
                                         origin.y + radius,
                                         origin.z + radius)
                                   )

    def point_in_shape(self, p: Point, t: float = 0) -> tuple[bool, float]:
        delta_to_point = p.distance_to(self._origin)
        if delta_to_point > self._radius:
            return False, 0

        solid_radius = self._radius * 0

        if delta_to_point < solid_radius:
            return True, 1

        return True, 1 - (delta_to_point - solid_radius) / (self._radius - solid_radius)

    def bounding_cube(self, t: float = 0) -> Cube:
        return self._bounding_cube


class CompositeShape(Shape):
    """
    Represents an abstract shape in 3D space
    :param shapes: required to be nonempty array
    :return:
    """

    def __init__(self, shapes: List[Shape]):
        """
        represents the union of shapes in shapes
        :param shapes:
        """
        assert len(shapes) > 0
        min_x = math.inf
        min_y = math.inf
        min_z = math.inf
        max_x = -math.inf
        max_y = -math.inf
        max_z = -math.inf

        for shape in shapes:
            bounding_cube = shape.bounding_cube()
            min_x = min(min_x, bounding_cube.x1)
            min_y = min(min_y, bounding_cube.y1)
            min_z = min(min_z, bounding_cube.z1)

            max_x = max(max_x, bounding_cube.x2)
            max_y = max(max_y, bounding_cube.y2)
            max_z = max(max_z, bounding_cube.z2)

        self._bounding_cube = Cube(Point(min_x, min_y, min_z),
                                   Point(max_x, max_y, max_z))

        self._shapes = shapes.copy()

    def point_in_shape(self, p: Point, t: float = 0) -> tuple[bool, float]:
        if p.x < self._bounding_cube.x1 \
                or p.x > self._bounding_cube.x2 \
                or p.y < self._bounding_cube.y1 \
                or p.y > self._bounding_cube.y2 \
                or p.z < self._bounding_cube.z1 \
                or p.z > self._bounding_cube.z2:
            return False, 0

        output_is_in_shape = False
        output_density = 0
        for shape in self._shapes:
            is_in_shape, density = shape.point_in_shape(p, t)
            if is_in_shape:
                output_is_in_shape = True
                if density == 1:
                    return True, 1
                output_density = max(density, output_density)

        return output_is_in_shape, output_density

    def bounding_cube(self) -> Cube:
        return self._bounding_cube


class GrowingAndShrinkingSphere(Shape):
    """
    A sphere that changes in size from max_radius to min_radius to
    max_radius repeatedly, taking <cycle_length> time to happen
    Also, the sphere is centered around <origin> in space.
    """

    def __init__(self, max_radius: float, min_radius: float,
                 cycle_length: float,
                 origin: Point = Point(0, 0, 0)):
        self._max_radius = max_radius
        self._min_radius = min_radius
        self._cycle_length = cycle_length
        self._origin = origin
        self._bounding_cube = Cube(
            origin.minus(Point(max_radius, max_radius, max_radius)),
            origin.minus(Point(-max_radius, -max_radius, -max_radius))
        )

    def point_in_shape(self, p: Point, t: float = 0) -> tuple[bool, float]:
        delta_to_point = p.distance_to(self._origin)
        t = t + self._cycle_length/2

        current_radius = self._min_radius + \
                         (utils.linear_on_zero_one(t*2* math.pi/self._cycle_length))*\
                         (self._max_radius - self._min_radius)

        if delta_to_point > current_radius:
            return False, 0

        solid_radius = current_radius * 0

        if delta_to_point < solid_radius:
            return True, 1

        return True, 1-(delta_to_point-solid_radius)/(current_radius-solid_radius)

    def bounding_cube(self) -> Cube:
        return self._bounding_cube