import math

from lightshow.lighting_language import *


def compile_to_csv(lightshow: LightShow, frequency: float, output_file_path: str, universe: int = 0) -> None:
    """
    Outputs csv of the form:
    note that h,s, and v are integers out of 255 in the output here
    <timestamp in millis>,lightNumber,h,s,v,lightNumber,h,s,v,.....
    <timestamp in millis>,lightNumber,h,s,v,lightNumber,h,s,v,.....
    <timestamp in millis>,lightNumber,h,s,v,lightNumber,h,s,v,.....

    :param universe: the lights for which we want to control in this universe
    :param output_file_path:
    :param frequency: the frequency (in hz) that we want to compile the lightshow to
    :param lightshow: the lightshow that we are compiling into a csv
    """

    max_time = math.ceil(lightshow.end)
    start_time = math.floor(lightshow.start)

    all_lights = lightshow.all_lights

    with open(output_file_path, "w") as output_file:
        t = start_time
        last_lighting_info = None
        while t < max_time:
            timestamp = int(t)  # round
            output_file.write(f'{timestamp}')
            t += 1000.0 / frequency
            lighting_info = lightshow.get_info_at(timestamp)
            for light, hsv_info in lighting_info.items():
                if light.universe != universe:
                    continue

                h = hsv_info.hsv.h
                s = hsv_info.hsv.s
                v = hsv_info.hsv.v

                if h is None:
                    h = 0
                if s is None:
                    s = 0
                if v is None:
                    v = 0

                h = int(h * 255)
                s = int(s * 255)
                v = int(v * 255)

                output_file.write(f',{light.light_number},{h},{s},{v}')

            if last_lighting_info is not None:
                for light in all_lights:
                    if light not in lighting_info and light in last_lighting_info and light.universe == universe:
                        output_file.write(f',{light.light_number},{0},{0},{0}')

            last_lighting_info = lighting_info
            output_file.write("\n")

        output_file.write(str(max_time))
        for light in all_lights:
            if light.universe == universe:
                output_file.write(f',{light.light_number},{0},{0},{0}')

        output_file.write("\n")
