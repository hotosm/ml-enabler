<template>
    <div class='col col--12 grid grid--gut12'>

        <label class='col col--12 pt12'>Bounding Box To Inference</label>
        <div class='col col--10 mb12'>
            <input v-model='bounds' type='text' class='input' placeholder='minX, minY, maxX, maxY'/>
        </div>
        <div class='col col--2 mb12'>
            <button @click='$emit("queue", poly)' class='btn btn--stroke round'>Submit</button>
        </div>

        <div id='map-container' class="col col--12 h600 w-full relative">
            <div id="map" class='w-full h-full'></div>
        </div>
    </div>
</template>

<script>
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

import MapboxGeocoder from '@mapbox/mapbox-gl-geocoder';
import '@mapbox/mapbox-gl-geocoder/dist/mapbox-gl-geocoder.css';

import MapboxDraw from '@mapbox/mapbox-gl-draw';
import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css';

import DrawRectangle from 'mapbox-gl-draw-rectangle-mode';

import bboxPolygon from '../../../node_modules/@turf/bbox-polygon/index.js';
import bbox from '../../../node_modules/@turf/bbox/index.js'

export default {
    name: 'StackMap',
    props: ['tilejson'],
    data: function() {
        return {
            map: false,
            token: false,
            bounds: '',
            poly: {
                type: 'Feature',
                properties: { },
                geometry: {
                    type: 'Polygon',
                    coordinates: [[[0,0],[0,0],[0,0],[0,0],[0,0]]]
                }
            }
        };
    },
    mounted: function() {
        fetch(window.api + `/v1/mapbox`, {
            method: 'GET'
        }).then((res) => {
            return res.json();
        }).then((res) => {
            this.token = res.token;
            this.init();
        });
    },
    watch: {
        bounds: function() {
            const bounds = this.bounds.split(',');

            try {
                this.poly = {
                    type: 'Feature',
                    properties: {},
                    geometry: bboxPolygon(bounds).geometry
                };

                this.map.getSource('bounds').setData(this.poly);

                this.map.fitBounds([
                    [bounds[0], bounds[1]],
                    [bounds[2], bounds[3]]
                ]);
            } catch(err) {
                // TODO make input bar red?
                console.error(err);
            }
        }
    },
    methods: {
        init: function() {
            mapboxgl.accessToken = this.token;

            this.map = new mapboxgl.Map({
                container: 'map',
                zoom: 1,
                style: 'mapbox://styles/mapbox/satellite-streets-v11'
            });

            this.map.addControl(new MapboxGeocoder({
                accessToken: mapboxgl.accessToken,
                mapboxgl: mapboxgl
            }));

            const modes = MapboxDraw.modes;
            modes.draw_rectangle = DrawRectangle;

            const draw = new MapboxDraw({
                displayControlsDefault: false,
                modes: modes
            });

            this.map.addControl(draw, 'top-left');
            draw.changeMode('draw_rectangle');

            this.map.on('draw.create', (f) => {
                this.bounds = bbox(f.features[0]).join(',');
                draw.deleteAll();
            });

            this.map.addControl(new mapboxgl.NavigationControl(), 'bottom-right');

            this.map.on('load', () => {
                this.map.addSource('bounds', {
                    type: 'geojson',
                    data: this.poly
                });

                this.map.addLayer({
                    'id': `bounds-layer`,
                    'type': 'fill',
                    'source': 'bounds',
                    'layout': {},
                    'paint': {
                        'fill-color': '#ff0000',
                        'fill-opacity': 0.5
                    }
                });
            });
        }
    }
}
</script>
