const FRAME_RATE = 60; // frames per second

import * as THREE from 'three';
import { OrbitControls } from 'https://unpkg.com/three@0.140.2/examples/jsm/controls/OrbitControls.js';

function addCubeconfig1(scene) {
    // has 4 strips that go from -5 to 5 with 10 cubes
    // strips are left --> right i,i+1... i+10
    const cubes = []
    const cubeGeometry = new THREE.BoxGeometry(.25, .25, .25);

    const num_rows = 8;
    const cubes_per_row = 20;
    for (let row = 0; row < num_rows; row++) {
        for (let col = 0; col < cubes_per_row; col++) {
            const material = new THREE.MeshPhysicalMaterial({ color: 0x000000,
            // transparent: true,
            // opacity:0.0
        });
            const cube = new THREE.Mesh(cubeGeometry, material);
            cubes.push(cube);
            scene.add(cube);
            cube.position.x = col * .5 - 5 + .25; // plus .5 is to center
            cube.position.y = row * .5;
            cube.position.z = -2;
        }
    }

    const single_cube_positions = [
        [-4.75, 3.5, -.5],
        [-4.35, 3, -.7],
        [-4.75, 3.25, 0],
        [-5.75, 3.5, -.5],
        [4.75, 3.5, -.5],
        [4.35, 3, -.7],
        [4.75, 3.25, 0],
        [5.75, 3.5, -.5],
    ]

    for (let [x, y, z] of single_cube_positions) {
        const material = new THREE.MeshPhysicalMaterial({ color: 0x000000, });
        const cube = new THREE.Mesh(cubeGeometry, material);
        cubes.push(cube);
        // cube.visible = false;
        scene.add(cube);
        cube.position.x = x;
        cube.position.y = y;
        cube.position.z = z;
    }


    return cubes
}

function addLightToScene(scene) {
    const light = new THREE.PointLight(0xffffff, 1);
    light.position.x = 0;
    light.position.y = 3;
    light.position.z = 7;
    scene.add(light);

    const ambient_light = new THREE.AmbientLight(0xaaaaaa); // soft white light
    scene.add(ambient_light);
}

function addAxesToScene(scene) {
    const axesHelper = new THREE.AxesHelper(5);
    scene.add(axesHelper);
}

class DataFetcherAndPlayer {
    all_data = []; // will be array of 2 values array of arrays of 4 values index, r,g,b
    running_clock = undefined;
    data_index = 0;
    current_data = [];

    constructor() {
    }

    // from https://stackoverflow.com/questions/17242144/javascript-convert-hsb-hsv-color-to-rgb-accurately
    HSVtoRGB(h, s, v) {
        var r, g, b, i, f, p, q, t;
        if (arguments.length === 1) {
            s = h.s, v = h.v, h = h.h;
        }
        i = Math.floor(h * 6);
        f = h * 6 - i;
        p = v * (1 - s);
        q = v * (1 - f * s);
        t = v * (1 - (1 - f) * s);
        switch (i % 6) {
            case 0: r = v, g = t, b = p; break;
            case 1: r = q, g = v, b = p; break;
            case 2: r = p, g = v, b = t; break;
            case 3: r = p, g = q, b = v; break;
            case 4: r = t, g = p, b = v; break;
            case 5: r = v, g = p, b = q; break;
        }
        return {
            r: r,
            g: g,
            b: b,
        };
    }

    async initData() {
        // Also plays the audio
        let req = new XMLHttpRequest();
        req.open("GET", "/get-data", true);
        const webserver_this = this;

        req.onload = function (e) {
            let server_response_string = req.responseText.trim();
            const per_line = server_response_string.split("\n");
            for (const line of per_line) {
                const line_split = line.split(",").map((x) => parseInt(x));
                let i = 0;
                const line_info = [NaN, []] // timestamp, [i,r,g,b]
                let light_index, h, s, v = 0;
                for (const value of line_split) {
                    if (isNaN(value)) {
                        throw new Error("got NaN value");

                    }
                    if (i === 0) {
                        // we are at the timestamp
                        line_info[0] = value;
                    } else if (i % 4 == 1) {
                        // light index
                        light_index = value;
                    } else if (i % 4 == 2) {
                        // h
                        h = value;
                    } else if (i % 4 == 3) {
                        // s
                        s = value;
                    } else if (i % 4 == 0) {
                        // v
                        v = value;
                        let rgb = webserver_this.HSVtoRGB(h / 255.0, s / 255.0, v / 255.0);
                        line_info[1].push([light_index, rgb.r, rgb.g, rgb.b]);
                        // here we should dump stuff into the data
                    }
                    i++;
                }
                webserver_this.all_data.push(line_info);

                document.getElementById("thebutton").addEventListener("click", (ev) => {
                    webserver_this.running_clock = new THREE.Clock();
                    webserver_this.running_clock.start();
                }, {
                    once: "true"
                });
            }
        }

        req.send();

        const addDotAndContinue = () => {
            const loading_button = document.getElementById("thebutton");
            loading_button.innerHTML += ".";
            if (webserver_this.all_data.length > 0){
                // we have recieved data
                loading_button.innerHTML = "Done! Click to begin"
            } else {
                setTimeout(
                    () => addDotAndContinue(),
                    1000,
                );
            }

        }

        addDotAndContinue();
    }

    getNextThing(current_time) {
        // expects current_time to be increasing
        if (this.running_clock === undefined){
            return [];
        }


        let currentRunTime = this.running_clock.getElapsedTime ()*1000;

        if (this.data_index >= this.all_data.length) {
            return [];
        }

        while (this.all_data[this.data_index][0] < currentRunTime - 100) {
            this.data_index += 1
            if (this.data_index >= this.all_data.length) {
                return [];
            }
        }

        if (currentRunTime <= this.all_data[this.data_index][0]) {
            return this.current_data;
        } else {
            this.current_data = this.all_data[this.data_index][1];

            this.data_index += 1;
            return this.current_data;
        }
        // Returns a list of [index,r,g,b]

    }
}

function main() {
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 4;
    camera.position.y = 5;
    camera.position.x = -7;
    camera.zoom = 2;
    camera.updateProjectionMatrix();
    const renderer = new THREE.WebGLRenderer({
        antialias: true
    });
    renderer.setClearColor(0x3e5261, 1);
    renderer.setSize(window.innerWidth*.8, window.innerHeight*.8);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    document.getElementById("render-div").appendChild(renderer.domElement);

    window.addEventListener("resize", () => {
        camera.aspect = window.innerWidth / window.innerHeight

        camera.updateProjectionMatrix()

        renderer.setSize(window.innerWidth, window.innerHeight)
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    });

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(-2, 1.5, -2);
    controls.update();

    const cubes = addCubeconfig1(scene);
    addLightToScene(scene);
    // addAxesToScene(scene);

    const dataThing = new DataFetcherAndPlayer()
    dataThing.initData();

    const tick = (current_time) => {


        // Limit to 30 fps to save my laptop
        setTimeout(() => window.requestAnimationFrame(tick), 1000 / FRAME_RATE);

        for (const [i, r, g, b] of dataThing.getNextThing(current_time)) {
            cubes[i].material.color.setRGB(r, g, b);
            // cubes[i].material.opacity = (r + g + b) / 3.0;
        }
        renderer.render(scene, camera);
    }

    window.requestAnimationFrame(tick);


}

main();