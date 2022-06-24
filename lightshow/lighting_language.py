from lightshow.core.types import *
from lightshow.core.lightshows import During, Fade, Together, PostModifier, RepeatAt, DynamicAtEvents, At, Strobe, OnShapes, \
    Mover
from typing import Iterable, Optional, Callable
from lightshow.core.utils import resolve_two_infos, importance_modifier, linear_on_zero_one


def at(time_offset: float, lightshow: LightShow) -> LightShow:
    """
    Basically shifts the entire show to play at time +time_offset from the original time
    :param time_offset: the time, in millis to offset the show
    :param lightshow: the lightshow to shift
    :return: A lightshow that starts at time <time_offset> instead of the original time of zero
    """
    return At(lightshow, time_offset)

def during(start: float, end: float, lightshow:float) -> LightShow:
    """
    Returns a lightshow that is deactivated outside the range of [start, end]
    Does not timeshift (unlike at())
    """
    return During(start, end, lightshow)


def together(lightshows: Iterable[LightShow]) -> LightShow:
    """
    A lightshow that plays all the lightshows in the input <lightshows> together at once, in a single lightshow,
    resolving conflicts by using relative importance at a given timestamp

    :param lightshows: the lightshows that are to be played together
    :return: a new lightshow representing all the other lightshows glued together
    """
    return Together(list(lightshows))


def fade(start_value: HSV, end_value: HSV, length: float, lights: Optional[Set[Light]] = None) -> LightShow:
    """

    :param lights: Set of lights to control (if non, just controls the zero generic light)
    :param start_value: the starting HSV value
    :param end_value: the ending HSV value, requires that end_value.{hsv} is None iff start_value.{hsv} is None
    :param length: the length of the light show
    :return: a lightshow fading from start value to end value. Uses RGB interpolation iff all of H/S/V defined
    """
    if lights is None:
        return Fade(length, {Light(0, is_generic=True)}, start_value, end_value)
    else:
        return Fade(length, lights, start_value, end_value)


def constant(color: HSV, length: float, lights: Optional[Set[Light]] = None) -> LightShow:
    """
    Returns a constant light show of color <color> that is over the time interval [0, <length>] and controls <lights>

    By default, the only light controlled is the generic zero light
    :param color:
    :param length:
    :param lights:
    :return:
    """
    if lights is None:
        return fade(color, color, length, {Light(0, is_generic=True)})
    else:
        return fade(color, color, length, lights)


def strobe(high_value: HSV, low_value: HSV, length: float,
           lights: Optional[Set[Light]],
           time_high: Optional[float] = None, time_low: Optional[float] = None,
           frequency: Optional[float] = None) -> LightShow:
    """

    :param lights:
    :param hi_value:
    :param lo_value:
    :param length:
    :param time_hi:
    :param time_lo:
    :param frequency:
    :return:
    """
    assert (time_high is not None and time_low is not None) or frequency is not None

    if lights is None:
        lights = Light(0, 0, is_generic=True)

    if frequency is not None:
        half_cycle_time_millis = (1000.0 / frequency) / 2.0
        return Strobe(lights, high_value, low_value, half_cycle_time_millis, half_cycle_time_millis, length)
    else:
        return Strobe(lights, high_value, low_value, time_high, time_low, length)


def new_controls(control_definition: Callable[[Light], Set[Light]], lightshow: LightShow) -> LightShow:
    """
    Sets lights to control new things
    :param control_definition:
    :param lightshow:
    :return:
    """

    def output_modifier(old_infos: LightingInfoType) -> LightingInfoType:
        new_infos = dict()

        for light, hsv_info in old_infos.items():
            for new_light in control_definition(light):
                if new_light not in new_infos:
                    new_infos[new_light] = hsv_info
                else:
                    new_infos[new_light] = resolve_two_infos(
                        hsv_info, new_infos[new_light])

        return new_infos

    new_lights = set()
    for old_light in lightshow.all_lights:
        new_lights |= control_definition(old_light)

    return PostModifier(lightshow, output_modifier, lambda x: new_lights)


def with_importance(importance: int, lightshow: LightShow) -> LightShow:
    """
    Makes a new lightshow with importance values set to the input

    :param lightshow: the lightshow to use to generate the new lightshow
    :param importance: integer >= 0, the importance of the new light show values
    :return: a lightshow where for all non-None values (h,s,v), the importance of that value is equal to <importance>
    """
    return PostModifier(lightshow,
                        info_modifier=lambda old_infos: importance_modifier(
                            old_infos, importance),
                        all_lights_modifier=lambda x: x)  # identity


def repeat_at(timestamps: Iterable[float], lightshow: LightShow) -> LightShow:
    """
    Repeats a given lightshow at the given offsets; conflicts are considered unspecified (since they have the same
     importance)
    :param timestamps: the offsets that we want the lightshow to repeat at
    :param lightshow: the lightshow to repeat
    :return: the new lightshow
    """
    # return Together(list(map(lambda x: Delay(lightshow, x), timestamps)))
    return RepeatAt(timestamps, lightshow)


def concat(lightshows: Iterable[LightShow]) -> LightShow:
    """
    :param lightshows: the lightshows to concat
    :return: a new lightshow that plays all the lightshows in <lightshows> one after another
    """
    total_offset = 0
    together_list = []

    for lightshow in lightshows:
        if total_offset == 0:
            together_list.append(lightshow)
        else:
            together_list.append(at(total_offset, lightshow))
        total_offset += lightshow.length

    return together(together_list)


def on_component(component: LightingComponent, lightshow: LightShow, control_light: Light = Light(0, is_generic=True)):
    """
    Uses the lightshow <lightshow> to control all the lights in <component>, based on the value of <control_light>
    """

    def info_modifier(old_info: LightingInfoType) -> LightingInfoType:
        new_info: LightingInfoType = {}
        if control_light in old_info:
            for light in component.all_lights_in_component():
                new_info[light] = old_info[control_light]
        return new_info

    def all_lights_modifier(old_lights: Set[Light]) -> Set[Light]:
        if control_light in old_lights:
            return component.all_lights_in_component()
        else:
            return set()

    return PostModifier(
        lightshow=lightshow,
        info_modifier=info_modifier,
        all_lights_modifier=all_lights_modifier
    )


def on_midi(midi_file_kwarg: str,
            light_show_on_midi: LightShow,
            pitch: int) -> LightShow:
    """
    Returns a lightshow that schedules lightshows to happen when the given midi first instrument hits a given pitch
    Most useful for drums/events
    :param pitch:
    :param light_show_on_midi:
    :param midi_file_kwarg: expects calls to on_audio such that **kwargs[midi_file_kwarg] = "location of midi file"
    :return:
    """

    def scheduler(**kwargs) -> Iterable[float]:
        assert midi_file_kwarg in kwargs

        import pretty_midi
        midi_file = kwargs[midi_file_kwarg]
        midi = pretty_midi.PrettyMIDI(midi_file)

        output = []

        if len(midi.instruments) == 0:
            return []

        for note in midi.instruments[0].notes:
            if note.pitch == pitch:
                output.append(note.start * 1000)

        return output

    return DynamicAtEvents(
        lightshow=light_show_on_midi,
        timestamp_generator=scheduler
    )


def on_shape(shape: Shape, lighting_component: LightingComponent, lightshow: LightShow,
             control_light: Light = Light(0, is_generic=True)) -> LightShow:
    """
    Basically just a wrapper around OnShapes to only control one shape/lighting component
    :param shape: the shape that we want to give the hsv value to
    :param lighting_component: the lighting component that we want the shape to apply on
    :param lightshow: the lightshow that controls the generic light for this shape
    :param control_light: the generic light to look for when determining the hsv value for the given shape
    :return: a LightShow where the lights in lighting component that are inside of shape are lit up with the value
        as determined by lightshow/shape/lighting_component
    """
    return OnShapes(
        lightshow=lightshow,
        controls={control_light: (shape, lighting_component)}
    )


def back_and_forth(start_location: Point, end_location: Point, time_to_move: float, shape: Shape,
                   lightshow: LightShow, lighting_component: LightingComponent,
                   control_light: Light = Light(0, 0, True)) -> LightShow:
    def position_controller(timestamp: float) -> Point:
        ratio_start = linear_on_zero_one(timestamp * math.pi * 2 / time_to_move)

        origin = Point(x=(1 - ratio_start) * start_location.x + ratio_start * end_location.x,
                       y=(1 - ratio_start) * start_location.y + ratio_start * end_location.y,
                       z=(1 - ratio_start) * start_location.z + ratio_start * end_location.z)

        return origin

    return Mover(   
        lighting_component=lighting_component,
        shape=shape,
        lightshow=lightshow,
        generic_light_to_use=control_light,
        position_controller=position_controller
    )
