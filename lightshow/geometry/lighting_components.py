from lightshow.core.types import *
from typing import Set, Optional, Iterable, List

class SingleLight(LightingComponent):
    """
    Represents a single light
    """

    def __init__(self, light: Light, location: Optional[Point] = None):
        super(SingleLight, self).__init__()
        self._light = light
        self._location = location

    def get_lights_in_space(self, shape: Shape, origin: Point, t: float = 0) -> Dict[Light, float]:
        if self._location is None:
            return dict()

        point_in_shape, density = shape.point_in_shape(self._location.minus(origin), t)
        if point_in_shape:
            return {self._light: density}

        return dict()

    def all_lights_in_component(self) -> Set[Light]:
        return {self._light}


class LightStrip(LightingComponent):
    """
    Represents a strip of lights

    Default location is along the x-axis of length, len(lights)

    start cannot equal end

    (0,0,0) --> (len(lights), 0,0)
    """

    def __init__(self, lights: List[Light],
                 start_location: Optional[Point] = None,
                 end_location: Optional[Point] = None):

        super(LightStrip, self).__init__()
        if start_location is None and end_location is not None:
            raise AssertionError("exactly one of start/end location is defined, should be none or both")

        if start_location is None:
            self.start_location = Point(0, 0, 0)
        else:
            self.start_location = start_location

        if end_location is None:
            self.end_location = Point(len(lights), 0, 0)
        else:
            self.end_location = end_location

        assert self.start_location != self.end_location

        self._lights = lights.copy()

    def get_lights_in_space(self, shape: Shape, origin: Point, t: float = 0) -> Dict[Light, float]:
        output = dict()

        for i in range(len(self._lights)):
            light = self._lights[i]
            ratio_end = i / (len(self._lights) - 1)
            point_to_query = Point(x=self.start_location.x * (1 - ratio_end) + self.end_location.x * ratio_end,
                                   y=self.start_location.y * (1 - ratio_end) + self.end_location.y * ratio_end,
                                   z=self.start_location.z * (1 - ratio_end) + self.end_location.z * ratio_end)

            point_in_shape, density = shape.point_in_shape(point_to_query.minus(origin), t)
            if point_in_shape:
                output[light] = density

        return output

    def all_lights_in_component(self) -> Set[Light]:
        return set(self._lights)

    @property
    def strip_length(self):
        """
        Euclidean distance from self.start_location to start.end_location
        :return: The length of the strip in space
        """
        dx = self.end_location.x - self.start_location.x
        dy = self.end_location.y - self.start_location.y
        dz = self.end_location.z - self.start_location.z

        return math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

class LightingComponentGroup(LightingComponent):
    """
    Represents a group of lighting components, passed in as an iterable
    """

    def __init__(self, components: Iterable[LightingComponent]):
        super(LightingComponentGroup, self).__init__()
        self._components = list(components)

    def get_lights_in_space(self, shape: Shape, origin: Point, t: float = 0) -> Dict[Light, float]:
        all_lights_in_space = dict()

        for component in self._components:
            lights_in_space = component.get_lights_in_space(shape, origin, t)
            for light in lights_in_space:
                if light not in all_lights_in_space:
                    all_lights_in_space[light] = lights_in_space[light]
                else:
                    all_lights_in_space[light] = max(lights_in_space[light], all_lights_in_space[light])

        return all_lights_in_space

    def all_lights_in_component(self) -> Set[Light]:
        all_lights_in_component = set()

        for component in self._components:
            all_lights_in_component |= component.all_lights_in_component()

        return all_lights_in_component