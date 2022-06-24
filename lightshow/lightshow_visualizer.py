from lightshow.lighting_language import *
import pyglet
import pyglet.shapes as shapes
import time
import colorsys
from lightshow.core.utils import *


class Visualizer:
    def __init__(self, light_show: LightShow):
        self._light_show = light_show
        self._beginning_time = time.time()

    def start(self, start_time: int = 0, number_of_circles=None) -> None:
        """
        :param start_time: time to start playing at, in millis
        :param number_of_circles:
        """
        window = pyglet.window.Window(resizable=True)
        self._beginning_time = time.time() - start_time / 1000

        batch = pyglet.graphics.Batch()

        circles = []

        max_light_index = 0

        for light in self._light_show.all_lights:
            if light.light_number > max_light_index:
                max_light_index = light.light_number

        num_circles = max_light_index + 1
        if number_of_circles is not None:
            num_circles = number_of_circles

        min_dimension = min(window.width, window.height)
        padding = 10
        circles_per_row = math.ceil(math.sqrt(num_circles))
        circle_radius = (min_dimension - padding * 2) / (circles_per_row * 2)
        circle_diameter = (min_dimension - padding * 2) / \
            (circles_per_row * 2) * 2
        for i in range(num_circles):
            circles.append(shapes.Circle(circle_diameter * (i % circles_per_row) + circle_radius + padding,
                                         circle_diameter *
                                         (i // circles_per_row) +
                                         circle_radius + padding,
                                         radius=circle_radius, batch=batch,
                                         color=(10, 10, 10)))

        @window.event
        def on_resize(width, height):
            min_dimension = min(width, height)
            padding = 10
            circles_per_row = math.ceil(math.sqrt(num_circles))
            circle_radius = (min_dimension - padding * 2) / \
                (circles_per_row * 2)
            circle_diameter = (min_dimension - padding * 2) / \
                (circles_per_row * 2) * 2
            for i in range(num_circles):
                circle = circles[i]
                circle.x = circle_diameter * \
                    (i % circles_per_row) + circle_radius + padding
                circle.y = circle_diameter * \
                    (i // circles_per_row) + circle_radius + padding
                circle.radius = circle_radius

        @window.event
        def on_key_press(symbol, modifiers):
            if symbol == pyglet.window.key.R:
                self._beginning_time = time.time() - start_time / 1000

                for circle in circles:
                    circle.color = (10, 10, 10)

        def draw(delta):
            current_time = time.time()
            delta_time = (current_time - self._beginning_time) * \
                1000  # since we want milliseconds

            for circle in circles:
                circle.color = (10, 10, 10)

            lighting_info = self._light_show.get_info_at(delta_time)

            for lightObj, hsv_info in lighting_info.items():
                hsv = hsv_info.hsv
                assert not (
                    hsv.h is None or hsv.s is None or hsv.v is None),\
                    f'something bad, got {hsv.h},{hsv.s},{hsv.v} at timestamp {delta_time}'
                r, g, b = colorsys.hsv_to_rgb(hsv.h, hsv.s, hsv.v)
                r = int(r * 255)
                g = int(g * 255)
                b = int(b * 255)
                circles[lightObj.light_number].color = (r, g, b)

            window.clear()
            batch.draw()

        pyglet.clock.schedule(draw)

        pyglet.app.run()


if __name__ == "__main__":

    lightshow = fade(HSV(1, 1, 1), HSV(1, 1, 0), length=10000,
                     lights={Light(0), Light(5)})
    
    Visualizer(lightshow).start(number_of_circles=25)
