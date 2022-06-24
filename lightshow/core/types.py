# This file contains the interfaces and record types used in the package
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Dict, Set
import math


class HSV:
    """
    Immutable type representing HSV values
    """

    def __init__(self,
                 h: Optional[float],
                 s: Optional[float],
                 v: Optional[float]):
        assert all(map(lambda x: x is None or 0 <= x <= 1, [h, s, v]))
        self._h = h
        self._s = s
        self._v = v

    # Using properties to reduce likelihood that we accidentally modify HSV values.
    @property
    def h(self) -> Optional[float]:
        return self._h

    @property
    def s(self) -> Optional[float]:
        return self._s

    @property
    def v(self) -> Optional[float]:
        return self._v

    def __eq__(self, other):
        return isinstance(other, HSV) \
            and self.h == other.h \
            and self.s == other.s \
            and self.v == other.v

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash((self.h, self.s, self.v))


class HSVInfo:
    """
    Immutable.

    Represents a new hsv info object, which contains hsv values as well as importance levels

    By default, importance is zero.
    """

    def __init__(self,
                 hsv: HSV,
                 h_importance: int = 0,
                 s_importance: int = 0,
                 v_importance: int = 0):
        self._hsv = hsv
        self._h_importance = h_importance
        self._s_importance = s_importance
        self._v_importance = v_importance

    @property
    def h_importance(self) -> int:
        return self._h_importance

    @property
    def s_importance(self) -> int:
        return self._s_importance

    @property
    def v_importance(self) -> int:
        return self._v_importance

    @property
    def hsv(self) -> HSV:
        return self._hsv

    def __eq__(self, other):
        return isinstance(other, HSVInfo) \
            and self.hsv == other.hsv \
            and self.h_importance == other.h_importance \
            and self.s_importance == other.s_importance \
            and self.v_importance == other.v_importance

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash((self.hsv, self.h_importance, self.s_importance, self.v_importance))


class Light:
    """
    Represents a Light Object, which has a lightNumber

    """

    def __init__(self, light_number: int, universe: int = 0, is_generic: bool = False):
        self._light_number = light_number
        self._universe = universe
        self._is_generic = is_generic

    @property
    def light_number(self) -> int:
        return self._light_number

    @property
    def universe(self) -> int:
        return self._universe

    @property
    def is_generic(self) -> bool:
        return self._is_generic

    def __eq__(self, other):
        return isinstance(other,
                          Light) and other.light_number == self.light_number and other.universe == self.universe \
            and other.is_generic == self.is_generic

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.light_number, self.universe))


# Maps each light to its corresponding info
LightingInfoType = Dict[Light, HSVInfo]


class LightShow(ABC):
    """
    Immutable type representing light shows
    """
    total_objects_created = 0

    def __init__(self):
        super(LightShow, self).__init__()
        LightShow.total_objects_created += 1

    @abstractmethod
    def get_info_at(self, timestamp: float) -> LightingInfoType:
        """
        Returns the value for a given light (based on index) controlled by the lightshow at the timestamp.
        :param timestamp: timestamp the time that we want the information for (in milliseconds)
        :return: lighting info with the HSV value (in [0,1]) of the given light index (as controlled by this LightShow).
            IFF the light is not controlled by the show at that timestamp for one or more of the H/S/V values, that
            value will be None in the value.

        i.e. If we get back a map that has Light(5) -> {h:.5,
        """
        pass

    @property
    @abstractmethod
    def length(self) -> float:
        """
        :return: self.end - self.start
        """
        pass

    @property
    @abstractmethod
    def start(self) -> float:
        """
        :return: the first time (in millis) where this light show might control at least one light
        (i.e there does not exist time t < return value such that get_info_at(t) gives a non empty map
        """
        pass

    @property
    @abstractmethod
    def end(self) -> float:
        """
        :return: the last time (in millis) where this light might control at least one light
        (i.e. there does not exist time t > return value such that get_info_at(t) gives a non-empty map
        """
        pass

    @property
    @abstractmethod
    def all_lights(self) -> Set[Light]:
        """
        :return: a set of all the lights that might ever be controlled by this light show
        (lights may not actually be controlled, but sometimes functions are structured abstractly in a case that we
        cannot know that; i.e. at every beat, but what if there are no beats? We may still return all lights controlled
        if there were a beat).
        """
        pass

    @abstractmethod
    def with_audio(self, audio_id: Optional[int] = None, **kwargs) -> LightShow:
        """
        Returns a new lightshow with the audio attached to it
        This only affects shows who depend on audio
        :param audio_id: the audio id of the information that we want to use (used for caching). If None, then no
            caching is used.
        :param kwargs; maps audio metadata label to information needed by audio callbacks.
            This information is generally up to the client, but needs to be consistent:
                I.e. if we have drum midi file at "./drum_file.mid", we might have a callback that expects
                "drum_midi_file" metadata. Kwargs should then contain drum_midi_file="./drum_file.mid"
        :return: the lightshow with the audio metadata incorporated. Note that this doesn't necessarily keep the
            structure the same (i.e. calling with_audio on the new audio might not generate the expected LightShow)
        """
        pass


class Point:
    def __init__(self, x: float = 0, y: float = 0, z: float = 0):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        return isinstance(other, Point) \
            and self.x == other.x \
            and self.y == other.y \
            and self.z == other.z

    def minus(self, other: Point) -> Point:
        return Point(self.x - other.x, self.y - other.y, self.z - other.z)

    def distance_to(self, other: Point):
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash((self.x, self.y, self.z))


class Shape(ABC):
    """
    Represents an abstract shape in 3D space
    Shapes can either be time invariant, or vary in time
        this is useful for representing things like an explosion, for instance (since the shape changes with time)
    """

    @abstractmethod
    def point_in_shape(self, p: Point, t: float = 0) -> tuple[bool, float]:
        """
        Returns whether the point is in the shape, and if so, how strongly in the shape the point is
        Strength is in [0,1]
        :param t: the time that we want the shape information at
        :param p:
        :return:
        """
        pass

    @abstractmethod
    def bounding_cube(self) -> Cube:
        """
        :return: The bounding cube of the shape across all of time (useful for optimizations)
        """
        pass


class Cube(Shape):
    """
    Represents a cube in space, x1, y1, z1 all less than x2,y2,z2 (regardless of input)
    """

    def __init__(self, p1: Point, p2: Point):
        """
        No restriction on the input, but resulting cube will have x1,y1,z1 as smaller than the 2s
        """
        super(Cube, self).__init__()
        self.x1 = min(p1.x, p2.x)
        self.y1 = min(p1.y, p2.y)
        self.z1 = min(p1.z, p2.z)
        self.x2 = max(p1.x, p2.x)
        self.y2 = max(p1.y, p2.y)
        self.z2 = max(p1.z, p2.z)

    def point_in_shape(self, p: Point, t: float = 0) -> tuple[bool, float]:
        if self.x1 <= p.x <= self.x2 and \
                self.y1 <= p.y <= self.y2 and \
                self.z1 <= p.z <= self.z2:
            return True, 1

        return False, 0

    def bounding_cube(self) -> Cube:
        return self


class LightingComponent(ABC):
    """
    Represents a collection of Lights, potentially with some geometry encoded.
    """

    def __init__(self):
        super(LightingComponent, self).__init__()

    @abstractmethod
    def get_lights_in_space(self, shape: Shape, origin: Point, t: float = 0) -> Dict[Light, float]:
        """
        Returns the lights contained in the bounding cube
        :param t: The time for which we want to consider the lights in the component (since lights may be moving)
        :param origin: the origin for which to use to offset the shape (i.e. a sphere around 0,0,0 passed in with origin
         of 1,1,1 would be the same as just the sphere with origin around 1,1,1;
         useful for reusing shapes in different parts of space)
        :param shape: the lights that we want to check  
        :return: the set of lights that are withing the bounds of the shape (inclusive), with the density for each one
        """
        pass

    @abstractmethod
    def all_lights_in_component(self) -> Set[Light]:
        pass
