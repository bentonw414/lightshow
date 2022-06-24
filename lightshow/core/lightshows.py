from lightshow.core.types import *
from typing import Any, Set, Optional, Iterable, Tuple, List, Callable
import colorsys
import bisect
import lightshow.core.utils as utils


class Fade(LightShow):
    """
    A light show that controls the lights <_lights> to fade from <_startValue> to <_endValue> over the course
    of [0,self.length)

    Uses RGB Interpolation when all of h,s, and v values are given, otherwise uses linear interpolation
    """

    def __init__(self, length: float, lights: Set[Light], start_value: HSV, end_value: HSV):
        super(Fade, self).__init__()
        self._length = length
        self._lights = lights.copy()
        self._start_value = start_value
        self._end_value = end_value
        self._rep_is_valid_check()
        self._interpolate_rgb = start_value.h is not None and start_value.s is not None and start_value.v is not None

    def _rep_is_valid_check(self) -> None:
        count_not_controlled = 0

        # Should have matching uncontrolled
        if self._start_value.h is None:
            assert (self._end_value.h is None)
            count_not_controlled += 1
        else:
            assert (self._end_value.h is not None)

        if self._start_value.s is None:
            assert (self._end_value.s is None)
            count_not_controlled += 1
        else:
            assert (self._end_value.s is not None)

        if self._start_value.v is None:
            assert (self._end_value.v is None)
            count_not_controlled += 1
        else:
            assert (self._end_value.v is not None)

        # Shouldn't be interpolating between nothing
        assert count_not_controlled < 3

    @staticmethod
    def _hsv_to_rgb_value(hsv_value: HSV) -> Tuple[float, float, float]:
        """
        Private method to convert hsv to rgb for interpolating the fade
        :param hsv_value:
        :return: a tuple of r,g,b
        """
        h = hsv_value.h
        s = hsv_value.s
        v = hsv_value.v

        return colorsys.hsv_to_rgb(h, s, v)

    @staticmethod
    def _rgb_to_hsv_value(r: float, g: float, b: float) -> Tuple[float, float, float]:
        """
        Private method to convert hsv to rgb for interpolating the fade
        :param r: the r channel input
        :param g: the g channel input
        :param b: the b channel input
        :return: a tuple of r,g,b
        """

        return colorsys.rgb_to_hsv(r, g, b)

    def get_info_at(self, timestamp: float) -> LightingInfoType:
        lighting_info = dict()
        if not self.start <= timestamp <= self.end:
            return lighting_info

        start_delta = timestamp - self.start
        percentage_start = 1.0 - start_delta / self.length

        if self._interpolate_rgb:
            start_r, start_g, start_b = Fade._hsv_to_rgb_value(self._start_value)
            end_r, end_g, end_b = Fade._hsv_to_rgb_value(self._end_value)

            output_r = percentage_start * start_r + (1.0 - percentage_start) * end_r
            output_g = percentage_start * start_g + (1.0 - percentage_start) * end_g
            output_b = percentage_start * start_b + (1.0 - percentage_start) * end_b

            h, s, v = Fade._rgb_to_hsv_value(output_r, output_g, output_b)

            for light in self._lights:
                lighting_info[light] = HSVInfo(HSV(h, s, v))

            return lighting_info

        else:
            h = None
            s = None
            v = None

            if self._start_value.h is not None:
                h = percentage_start * self._start_value.h + (1.0 - percentage_start) * self._end_value.h
            if self._start_value.s is not None:
                s = percentage_start * self._start_value.s + (1.0 - percentage_start) * self._end_value.s
            if self._start_value.v is not None:
                v = percentage_start * self._start_value.v + (1.0 - percentage_start) * self._end_value.v

            for light in self._lights:
                lighting_info[light] = HSVInfo(HSV(h, s, v))

            return lighting_info

    @property
    def length(self) -> float:
        return self._length

    @property
    def start(self) -> float:
        return 0

    @property
    def end(self) -> float:
        return self.length

    @property
    def all_lights(self) -> Set[Light]:
        return self._lights.copy()

    def with_audio(self, audio_id: Optional[int] = None, **kwargs) -> LightShow:
        return self


class Strobe(LightShow):

    def __init__(self, lights: Set[Light],
                 hi_value: HSV, lo_value: HSV,
                 time_hi: float, time_lo: float,
                 length: float):
        super(Strobe, self).__init__()
        self._lights = lights.copy()
        self._hi_value = hi_value
        self._lo_value = lo_value
        self._time_hi = time_hi
        self._time_lo = time_lo
        self._length = length

    def get_info_at(self, timestamp: float) -> LightingInfoType:
        if timestamp < self.start or timestamp >= self.end:
            return {}

        time_stamp_in_cycle = timestamp % (self._time_hi + self._time_lo)

        if time_stamp_in_cycle < self._time_hi:
            hsv = self._hi_value
        else:
            hsv = self._lo_value

        output = {}

        for light in self._lights:
            output[light] = HSVInfo(hsv)

        return output

    @property
    def length(self) -> float:
        return self._length

    @property
    def start(self) -> float:
        return 0

    @property
    def end(self) -> float:
        return self.length

    @property
    def all_lights(self) -> Set[Light]:
        return self._lights.copy()

    def with_audio(self, audio_id: Optional[int] = None, **kwargs) -> LightShow:
        return self

    def __hash__(self):
        pass

    def __eq__(self, other):
        pass


class At(LightShow):
    """
    A lightshow that starts at time <time_offset> instead of the original time of zero

    Basically shifts the entire show to play at time +time_offset from the original time
    """

    def __init__(self, lightshow: LightShow, time_offset: float):
        super(At, self).__init__()
        self._lightshow = lightshow
        self._time_offset = time_offset
        self._audio_cache: Dict[int, LightShow] = {}

    def get_info_at(self, timestamp: float) -> LightingInfoType:
        return self._lightshow.get_info_at(timestamp - self._time_offset)

    @property
    def length(self) -> float:
        return self._lightshow.length

    @property
    def start(self) -> float:
        return self._lightshow.start + self._time_offset

    @property
    def end(self) -> float:
        return self._lightshow.end + self._time_offset

    @property
    def all_lights(self) -> Set[Light]:
        return self._lightshow.all_lights

    def with_audio(self, audio_id: Optional[int] = None, **kwargs) -> LightShow:
        if audio_id is not None and audio_id in self._audio_cache:
            return self._audio_cache[audio_id]

        with_audio_output = At(self._lightshow.with_audio(audio_id, **kwargs), self._time_offset)

        if audio_id is not None:
            self._audio_cache[audio_id] = with_audio_output

        return with_audio_output


class During(LightShow):
    """
    A lightshow that deactivates another lightshow when it is not within [<start>, <end>]
    """

    def __init__(self, start: float, end: float, lightshow: LightShow):
        super(During, self).__init__()
        self._start = start
        self._end = end
        self._lightshow = lightshow
        self._audio_cache: Dict[int, LightShow] = {}

    def get_info_at(self, timestamp: float) -> LightingInfoType:
        if timestamp < self._start or timestamp > self._end:
            return dict()

        return self._lightshow.get_info_at(timestamp)

    @property
    def length(self) -> float:
        return self.end - self.start

    @property
    def start(self) -> float:
        return max(self._lightshow.start, self._start)

    @property
    def end(self) -> float:
        return min(self._lightshow.end, self._end)

    @property
    def all_lights(self) -> Set[Light]:
        return self._lightshow.all_lights

    def with_audio(self, audio_id: Optional[int] = None, **kwargs) -> LightShow:
        if audio_id is not None and audio_id in self._audio_cache:
            return self._audio_cache[audio_id]

        with_audio_output = During(self._start, self._end, self._lightshow.with_audio(audio_id, **kwargs))

        if audio_id is not None:
            self._audio_cache[audio_id] = with_audio_output

        return with_audio_output


class Together(LightShow):
    """
    A lightshow that plays all the lightshows in the input <lightshows> together at once, in a single lightshow,
    resolving conflicts by using relative importance at a given timestamp.
    """

    def __init__(self, lightshows: List[LightShow]):
        super(Together, self).__init__()
        assert len(lightshows) > 0
        self._lightshows = lightshows.copy()
        self._audio_cache: Dict[int, LightShow] = {}

    def get_info_at(self, timestamp: float) -> LightingInfoType:
        from lightshow.core.utils import resolve_two_infos
        total_output = dict[Light, HSVInfo]()

        for lightshow in self._lightshows:
            potential_info = lightshow.get_info_at(timestamp)
            for light, hsv_info in potential_info.items():
                if light not in total_output:
                    total_output[light] = hsv_info
                else:
                    current_proposed_info = total_output[light]

                    total_output[light] = resolve_two_infos(current_proposed_info, hsv_info)

        return total_output

    @property
    def length(self) -> float:
        return self.end - self.start

    @property
    def start(self) -> float:
        return min(map(lambda lightshow: lightshow.start, self._lightshows))

    @property
    def end(self) -> float:
        return max(map(lambda lightshow: lightshow.end, self._lightshows))

    @property
    def all_lights(self) -> Set[Light]:
        output = set[Light]()

        for lightshow in self._lightshows:
            output |= lightshow.all_lights
        return output

    def with_audio(self, audio_id: Optional[int] = None, **kwargs) -> LightShow:
        if audio_id is not None and audio_id in self._audio_cache:
            return self._audio_cache[audio_id]

        with_audio_output = Together(
            list(map(lambda lightshow: lightshow.with_audio(audio_id, **kwargs), self._lightshows)))

        if audio_id is not None:
            self._audio_cache[audio_id] = with_audio_output

        return with_audio_output


class RepeatAt(LightShow):
    """
    Repeats a show at a given time
    """

    def __init__(self, timestamps: Iterable[float], lightshow: LightShow):
        super(RepeatAt, self).__init__()
        self._lightshow = lightshow
        self._lightshow_length = lightshow.length
        self._timestamps = list(timestamps)
        self._timestamps.sort()
        self._audio_cache: Dict[int, LightShow] = {}

    def get_info_at(self, timestamp: float) -> LightingInfoType:
        start_index = bisect.bisect_left(self._timestamps, timestamp - self._lightshow_length) - 1
        end_index = bisect.bisect_right(self._timestamps, timestamp + self._lightshow_length)

        start_index = max(0, start_index)

        from lightshow.core.utils import resolve_two_infos
        total_output = dict[Light, HSVInfo]()

        for timestamp_off in self._timestamps[start_index:end_index + 1]:
            potential_info = self._lightshow.get_info_at(timestamp - timestamp_off)
            for light, hsv_info in potential_info.items():
                if light not in total_output:
                    total_output[light] = hsv_info
                else:
                    current_proposed_info = total_output[light]

                    total_output[light] = resolve_two_infos(hsv_info, current_proposed_info)

        return total_output

    @property
    def length(self) -> float:
        return self.end - self.start

    @property
    def start(self) -> float:
        return min(self._timestamps) + self._lightshow.start

    @property
    def end(self) -> float:
        return max(self._timestamps) + self._lightshow.end

    @property
    def all_lights(self) -> Set[Light]:
        return self._lightshow.all_lights

    def with_audio(self, audio_id: Optional[int] = None, **kwargs) -> LightShow:
        if audio_id is not None and audio_id in self._audio_cache:
            return self._audio_cache[audio_id]

        with_audio_output = RepeatAt(self._timestamps, self._lightshow.with_audio(audio_id, **kwargs))

        if audio_id is not None:
            self._audio_cache[audio_id] = with_audio_output

        return with_audio_output


class PostModifier(LightShow):
    """
    Represents a lightshow that modifies the returned values in some way
    Generally, this means modifying what "all_lights" are or modifying the returned LightingInfoType values

    The client provides both of these as callables.
    """

    def __init__(self, lightshow: LightShow,
                 info_modifier: Callable[[LightingInfoType], LightingInfoType],
                 all_lights_modifier: Callable[[Set[Light]], Set[Light]]):
        super(PostModifier, self).__init__()
        self._lightshow = lightshow
        self._info_modifier = info_modifier
        self._all_lights_modifier = all_lights_modifier
        self._audio_cache: Dict[int, LightShow] = {}

    def get_info_at(self, timestamp: float) -> LightingInfoType:
        return self._info_modifier(self._lightshow.get_info_at(timestamp))

    @property
    def length(self) -> float:
        return self._lightshow.length

    @property
    def start(self) -> float:
        return self._lightshow.start

    @property
    def end(self) -> float:
        return self._lightshow.end

    @property
    def all_lights(self) -> Set[Light]:
        return self._all_lights_modifier(self._lightshow.all_lights)

    def with_audio(self, audio_id: Optional[int] = None, **kwargs) -> LightShow:
        if audio_id is not None and audio_id in self._audio_cache:
            return self._audio_cache[audio_id]

        with_audio_output = PostModifier(self._lightshow.with_audio(audio_id, **kwargs), self._info_modifier,
                                         self._all_lights_modifier)

        if audio_id is not None:
            self._audio_cache[audio_id] = with_audio_output

        return with_audio_output


class DynamicAtEvents(LightShow):
    """
    Represents a show that uses audio analysis to repeat a light at certain times
    """

    def __init__(self, lightshow: LightShow,
                 timestamp_generator: Callable[[Any], Iterable[float]]):
        super(DynamicAtEvents, self).__init__()
        self._lightshow = lightshow
        self._timestamp_generator = timestamp_generator
        self._audio_cache: Dict[int, LightShow] = {}

    def get_info_at(self, timestamp: float) -> LightingInfoType:
        return {}

    @property
    def length(self) -> float:
        if len(self._audio_info) == 0:
            return 0
        return self._lightshow_calculator.length

    @property
    def start(self) -> float:
        if len(self._audio_info) > 0:
            return self._lightshow_calculator.start
        return 0

    @property
    def end(self) -> float:
        if len(self._audio_info) > 0:
            return self._lightshow_calculator.end
        return 0

    @property
    def all_lights(self) -> Set[Light]:
        if len(self._audio_info) == 0:
            return set()
        return self._lightshow_calculator.all_lights

    def with_audio(self, audio_id: Optional[int] = None, **kwargs) -> LightShow:
        if audio_id is not None and audio_id in self._audio_cache:
            return self._audio_cache[audio_id]

        times = list(self._timestamp_generator(**kwargs))
        
        with_audio_output = RepeatAt(times, self._lightshow)

        if audio_id is not None:
            self._audio_cache[audio_id] = with_audio_output

        return with_audio_output


class OnShapes(LightShow):
    """
    A light show is taken in and then the output uses each shape and lights that shape up on a LightingComponent
    """

    def __init__(self, lightshow: LightShow,
                 controls: Dict[Light, tuple[Shape, LightingComponent]]):
        super(OnShapes, self).__init__()

        for light in controls:
            assert light.is_generic

        self._controls = controls.copy()
        self._lightshow = lightshow

    def get_info_at(self, timestamp: float) -> LightingInfoType:
        lightshow_info = self._lightshow.get_info_at(timestamp)

        output: LightingInfoType = {}

        # for each controlled light, potentially map to its set of output lights
        for controlled_light in self._controls:
            shape, lighting_component = self._controls[controlled_light]
            if controlled_light in lightshow_info:
                # should this have an origin, or make that part of the shape
                lights_in_shape = lighting_component.get_lights_in_space(shape, Point(0, 0, 0), t=timestamp)
                for light in lights_in_shape:
                    without_density_info = lightshow_info[controlled_light]
                    potential_new_info = HSVInfo(
                        hsv=HSV(without_density_info.hsv.h,
                                without_density_info.hsv.s,
                                without_density_info.hsv.v
                                if without_density_info.hsv.v is None
                                else without_density_info.hsv.v * lights_in_shape[light]),
                        h_importance=without_density_info.h_importance,
                        s_importance=without_density_info.s_importance,
                        v_importance=without_density_info.v_importance
                    )
                    if light in output:
                        # TODO see if there is a refactoring that would make this less repetitive/clunky to code on the
                        # client side
                        output[light] = utils.resolve_two_infos(output[light], potential_new_info)
                        pass
                    else:
                        output[light] = potential_new_info

        return output

    @property
    def length(self) -> float:
        return self._lightshow.length

    @property
    def start(self) -> float:
        return self._lightshow.start

    @property
    def end(self) -> float:
        return self._lightshow.end

    @property
    def all_lights(self) -> Set[Light]:
        all_lights = set()
        for light in self._controls:
            all_lights |= self._controls[light][1].all_lights_in_component()

        return all_lights

    def with_audio(self, audio_id: Optional[int] = None, **kwargs) -> LightShow:
        return OnShapes(
            self._lightshow.with_audio(audio_id, **kwargs),
            self._controls
        )


class StateChangerShow(LightShow):
    """
    The callback generator maps to a label, which then should be in the dict, so that we know which lightshow state
    to run at that point.
    """

    def __init__(self, callback_generator: Callable[[float], Any], show_mapping: Dict[Any, LightShow]):
        super(StateChangerShow, self).__init__()
        self._callback_generator = callback_generator
        self._all_lights = set()
        self._show_mapping = show_mapping.copy()
        self._audio_cache: Dict[int, LightShow] = {}
        for show in show_mapping.values():
            self._all_lights |= show.all_lights

    def get_info_at(self, timestamp: float) -> LightingInfoType:
        return self._show_mapping[self._callback_generator(timestamp)].get_info_at(timestamp)

    @property
    def length(self) -> float:
        return math.inf

    @property
    def start(self) -> float:
        return 0

    @property
    def end(self) -> float:
        return math.inf

    @property
    def all_lights(self) -> Set[Light]:
        return self._all_lights.copy()

    def with_audio(self, audio_id: Optional[int] = None, **kwargs) -> LightShow:
        if audio_id is not None and audio_id in self._audio_cache:
            return self._audio_cache[audio_id]

        new_show_mapping = {}

        # Basically update the shows that we are mapping to
        for label in self._show_mapping:
            new_show_mapping[label] = self._show_mapping[label].with_audio(audio_id, **kwargs)

        with_audio_output = StateChangerShow(
            callback_generator=self._callback_generator,
            show_mapping=new_show_mapping,
        )

        if audio_id is not None:
            self._audio_cache[audio_id] = with_audio_output

        return with_audio_output


class Mover(LightShow):
    """
    Represents a lightshow that set all lights in <lighting_component> that are in a given <shape> to have the value
    given by the output of <lightshow> to generic_light_to_use at a given time.

    The shape can also optionally be moved using the <position_controller>, which moves the shape origin as a function
    of time.

    For perfomance purposes, this is only accurate to +- 5ms (so repeat uses of the show can be cached)
    """

    def __init__(self, lighting_component: LightingComponent, shape: Shape,
                 lightshow: LightShow,
                 generic_light_to_use: Light = Light(0, 0, True),
                 position_controller: Optional[Callable[[float], Point]] = None):
        super(Mover, self).__init__()

        assert generic_light_to_use.is_generic

        self._lighting_component = lighting_component
        self._shape = shape
        self._lightshow = lightshow
        self._position_controller = position_controller
        self._generic_light_to_use = generic_light_to_use
        self._audio_cache: Dict[int, LightShow] = {}
        self._output_cache: Dict[int, LightingInfoType] = {}

    def get_info_at(self, timestamp: float) -> LightingInfoType:
        timestamp = round(timestamp / 10) * 10
        if round(timestamp) in self._output_cache:
            return self._output_cache[round(timestamp)]

        if self._position_controller is None:
            origin = Point(0, 0, 0)
        else:
            origin = self._position_controller(timestamp)

        output_lights = self._lighting_component.get_lights_in_space(self._shape, origin, timestamp)
        hsv_info = self._lightshow.get_info_at(timestamp)

        output_info = {}

        if self._generic_light_to_use in hsv_info:
            for output_light in output_lights:
                old_info = hsv_info[self._generic_light_to_use]
                if old_info.hsv.v is not None:
                    # interpolate the value of the output
                    output_info[output_light] = HSVInfo(hsv=HSV(old_info.hsv.h,
                                                                old_info.hsv.s,
                                                                old_info.hsv.v * output_lights[output_light]),
                                                        h_importance=old_info.h_importance,
                                                        s_importance=old_info.s_importance,
                                                        v_importance=old_info.v_importance)
                else:
                    output_info[output_light] = old_info

        self._output_cache[round(timestamp)] = output_info
        return output_info

    @property
    def length(self) -> float:
        return self._lightshow.length

    @property
    def start(self) -> float:
        return self._lightshow.start

    @property
    def end(self) -> float:
        return self._lightshow.end

    @property
    def all_lights(self) -> Set[Light]:
        return self._lighting_component.all_lights_in_component()

    def with_audio(self, audio_id: Optional[int] = None, **kwargs) -> LightShow:
        if audio_id is not None and audio_id in self._audio_cache:
            return self._audio_cache[audio_id]

        with_audio_output = Mover(self._lighting_component,
                                  self._shape,
                                  self._lightshow.with_audio(audio_id, **kwargs),
                                  self._generic_light_to_use,
                                  self._position_controller)

        if audio_id is not None:
            self._audio_cache[audio_id] = with_audio_output

        return with_audio_output


class WithAlbumArtColors(LightShow):
    """
    Represents a new LightShow that modifies the output of each LightShow
    in <lightshows> to have colors given by 3 most dominant colors in the
    album art at the url <album_url_kwarg>
    """

    def __init__(self, lightshows: List[LightShow], album_url_kwarg: str):
        super(WithAlbumArtColors, self).__init__()
        self._lightshows = lightshows.copy()
        self._album_url_kwarg = album_url_kwarg
        self._with_audio_cache: Dict[int, LightShow] = {}

    def get_info_at(self, timestamp: float) -> LightingInfoType:
        return self._post_modifier.get_info_at(timestamp)

    @property
    def length(self) -> float:
        return max(map(lambda lightshow: lightshow.length, self._lightshows))

    @property
    def start(self) -> float:
        return min(map(lambda lightshow: lightshow.start, self._lightshows))

    @property
    def end(self) -> float:
        return max(map(lambda lightshow: lightshow.end, self._lightshows))

    @property
    def all_lights(self) -> Set[Light]:
        output = set()
        for lightshow in self._lightshows:
            output |= lightshow.all_lights
        return output

    def with_audio(self,audio_id:Optional[int]=None,**kwargs)->LightShow:
        if audio_id in self._with_audio_cache:
            return self._with_audio_cache[audio_id]

        import requests
        from PIL import Image

        album_cover_url = kwargs.get(self._album_url_kwarg)
        album_cover = Image.open(requests.get(
                                    album_cover_url,
                                    stream=True).raw)
        palette_img = album_cover.quantize(3, kmeans=3)

        # Find the colors that occurs most often
        palette = palette_img.getpalette()
        color_counts = sorted(palette_img.getcolors(), reverse=True)
        colors_hsv = []

        for i in range(3):
            palette_index = color_counts[i][1]
            dominant_color = palette[palette_index * 3:palette_index * 3 + 3]
            colors_hsv.append(
                colorsys.rgb_to_hsv(
                    dominant_color[0] / 255,
                    dominant_color[1] / 255,
                    dominant_color[2] / 255))

        album_color_covers = list(map(lambda hsv: 
                                    HSV(hsv[0],
                                    hsv[1], hsv[2]),
                                    colors_hsv))

        # Function for creating the various PostModifier functions
        def info_modifier_factory(index: int) -> Callable[[LightingInfoType],
                                                           LightingInfoType]:
            def info_modifier(old_info: LightingInfoType) -> LightingInfoType:
                new_info: LightingInfoType = {}
                index = index % len(album_color_covers)
                for light, info in old_info.items():
                    new_info[light] = HSVInfo(
                        hsv=HSV(album_color_covers[index].h,
                                album_color_covers[index].s,
                                info.hsv.v),
                        h_importance=info.h_importance,
                        s_importance=info.s_importance,
                        v_importance=info.v_importance
                    )
                return new_info

            return info_modifier

        # Make the various PostModifier objects
        together_list = []
        for i, lightshow in enumerate(self._lightshows):
            together_list.append(
                PostModifier(
                    lightshow=lightshow.with_audio(audio_id, **kwargs),
                    info_modifier=info_modifier_factory(i),
                    all_lights_modifier=lambda x: x
                )
            )

        new_output = Together(together_list)

        self._with_audio_cache[audio_id] = new_output
        return new_output
