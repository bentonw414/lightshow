from lightshow.core.types import HSV, HSVInfo, LightingInfoType
import math


def resolve_two_infos(hsv_info_1: HSVInfo, hsv_info_2: HSVInfo) -> HSVInfo:
    """
    Resolves two hsv infos based on importance
    If they have equal importance, then hsv_info_1 is prioritized
    :param hsv_info_1:
    :param hsv_info_2:
    :return:
    """
    output_h = hsv_info_2.hsv.h
    output_s = hsv_info_2.hsv.s
    output_v = hsv_info_2.hsv.v
    output_h_importance = hsv_info_2.h_importance
    output_s_importance = hsv_info_2.s_importance
    output_v_importance = hsv_info_2.v_importance

    if hsv_info_1.h_importance >= hsv_info_2.h_importance:
        output_h = hsv_info_1.hsv.h
        output_h_importance = hsv_info_1.h_importance

    if hsv_info_1.s_importance >= hsv_info_2.s_importance:
        output_s = hsv_info_1.hsv.s
        output_s_importance = hsv_info_1.s_importance

    if hsv_info_1.v_importance >= hsv_info_2.v_importance:
        output_v = hsv_info_1.hsv.v
        output_v_importance = hsv_info_1.v_importance

    return HSVInfo(HSV(output_h, output_s, output_v),
                   output_h_importance,
                   output_s_importance,
                   output_v_importance)


def importance_modifier(old_infos: LightingInfoType, importance) -> LightingInfoType:
    """
    Takes in lighting info and modifies the importance to have the new importance
    :param old_infos: the lighting info before
    :param importance: the new importance of values
    :return: new lighting info, where all non-None hsv values have {hsv}Importance = <importance>
    """
    new_infos = dict()

    for light, hsv_info in old_infos.items():
        new_info = HSVInfo(hsv_info.hsv,
                           h_importance=importance,
                           s_importance=importance,
                           v_importance=importance)
        new_infos[light] = new_info

    return new_infos


def linear_on_zero_one(x: float, cycle_length=2 * math.pi) -> float:
    """
    A function of cycle 2pi that linearly goes from 0 -> 1 -> 0 ...
    at zero, equals 0
    :param cycle_length:
    :param x:
    :return:
    """
    in_cycle = x % cycle_length

    out = 1 - abs(in_cycle - cycle_length / 2) / (cycle_length / 2)
    return out
