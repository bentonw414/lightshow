import pickle
from pathlib import Path
from random import randint, random
from typing import Dict, Any, List
import json
from bottle import route, run, template, static_file, post, request
from scipy import rand
from lightshow import compiler_examples
from lightshow.core.lightshows import WithAlbumArtColors
from lightshow.geometry.lighting_components import LightStrip, SingleLight
from lightshow.lighting_language import *
from lightshow.geometry.shapes import GrowingAndShrinkingSphere
import inspect

def lightshow1() -> LightShow:
    return fade(HSV(0,1,1), HSV(1,1,0), 10000)

class SimpleServer:
    def __init__(self, port: int, lightshow: LightShow,
                 audio_metadata: Optional[Dict[str, Any]] = None):
        self._lightshow = lightshow
        self._audio_metadata = audio_metadata

        @route("/public/<filename>")
        def handle_public_file(filename):
            public_path = str(Path(__file__).parent.absolute()) + "/public/"
            result = static_file(filename, root=public_path)
            result.set_header("Cache-Control", "no-cache")
            return result

        @route("/get-data")
        def handle_get_data():
            if self._audio_metadata is not None:
                show = self._lightshow.with_audio(0, **self._audio_metadata)
            else:
                show = self._lightshow
            compiled_path = str(Path(__file__).parent.absolute()) + "/compiled.csv"
            compiler_examples.compile_to_csv(show, 30, compiled_path)
            result = static_file(compiled_path, root="/")
            result.set_header("Cache-Control", "no-cache")
            return result

        run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    counting_up_indices = together([
        at(i*50, concat(
            [
            fade(HSV(.3,1,0), HSV(.3,1,1), 500, {Light(i)}),
            fade(HSV(.6,1,1), HSV(.6,1,0), 500, {Light(i)})
            ])
        ) for i in range(168)]
    )
    SimpleServer(port=8080,
                 lightshow=counting_up_indices)