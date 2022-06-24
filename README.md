# LightShow

This repo contains the code for the LightShow Python package. In depth information about this package can be found in the [thesis.pdf](./thesis.pdf) file at the root of the repo.

## Getting Started

In order to use this library, Python 3.9 is required.

In order to use the library in a Python project, please use the following method.

First, download or clone this repo, and add the location of the `lightshow` folder inside of this repo to the `PYTHONPATH` environment variable (this needs to be on the path in order for Python to find the code).

Then, choose how you want to visualize basic LightShows. If you want to visualize shows in a local window, you can use the `Visualizer` class located in `lightshow/light_visualizer.py`. Note that this will require install of the `pyglet` library (found [here](https://pyglet.org/)). If you want to visualize shows in browser, you can use the code written in `lightshow/simple_server.py.` See below for information on how to run the simple server.


## Basics

### LightShow

`LightShow` objects are the core of the LightShow package. This is implemented as an abstract base class, with a few core methods:
* `start`: this is the start time (in milliseconds) of the `LightShow`
* `end`: this is the end time of the `LightShow` (milliseconds)
* `length`: this is just the length of the light show (also ms)
* `get_info_at`: this gets the lighting values of a `LightShow` given a time.
* `with_audio`: this returns a new `LightShow`, initialized to use the metadata passed in as kwargs. See examples in the thesis document for how this works in practice.

Generally `LightShow` objects should be created using abstractions from `lightshow/lighting_language.py`, but if you want to implement more abstractions, then you can import `LightShow` classes from `lightshow/core/lightshows.py`. Note that you can also implement the `LightShow` abc to expand the language.

### Light

* This is the abstraction for a `Light` output by a `LightShow`, and contains `light_number`, `universe`, and `is_generic`. Generic lights are described in more detail in the paper, but generally are used for light outputs that are used as input to another show. The `light_number` is like a light index, but lights can also be in different universes (useful for representing shows that are controlled by different controllers, for instance).

### HSV and HSVInfo

HSV objects only contain an optional hue, saturation, and value in [0,1], whereas HSVInfo objects also associate an integer "importance" with each of those values.

### LightingInfoType

This is just an alias for `Dict[Light, HSVInfo]`.

### LightingComponent

`LightingComponents` are used to represent how lights sit in space or are grouped together, and generally have two methods. `get_lights_in_space` returns all of the lights inside of a given shape (with their densities), and `all_lights_in_component` returns just a set of all the Lights that are contained in the LightingComponent.

### Shape

A `Shape` represents a region in space (that has density which may vary over time). `point_in_shape` returns the density of the shape at a given point, and `bounding_cube` returns a `Cube` shape that bounds the region of space where the given `Shape` has density > 0 (across all of time).

### Simple Server Visualizer

In the `simple_visualizer` folder, there is a relatively simple web server that uses the `bottle` Python package to run a server that can render LightShows in the browser. The way to run this is by running the `server.py` file, and then navigating to `localhost:8080/public/index.html` (assuming the server is started on port 8080). The page will load, and then a button allows you to start the webserver playing in the 3D environment. This code is meant to be more of a template to show how the LightShow package might be used.

The `SimpleServer` just takes in a LightShow to play as well as a port to run the server on.

### Visualizer

The `Visualizer` constructor takes in a `LightShow` object to play, and then has one method, namely `start`. When `start` is called, it takes in the number of circles to display (or just uses the largest light index from the show). Note that the visualizer assumes that all lights are in universe zero, so using this visualizer with multiple universes may not work very well.

An example usage of the visualizer can be run by doing the following:
```py
lightshow = fade(HSV(1, 1, 1), HSV(1, 1, 0), length=10000,
                     lights={Light(0), Light(5)})
    
    Visualizer(lightshow).start(number_of_circles=25)
```

## Misc Notes

Note that the general `compiler_examples.py` file contains a method which allows to output from a `LightShow` to be compiled into a CSV representing the stream of HSV value outputs.
