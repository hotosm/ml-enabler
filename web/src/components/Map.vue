<template>
    <div class='col col--12 h600'>
        <div id='map-container' class="col col--12 h-full w-full relative">
            <div class='bg-white round absolute top left z5 px12 py12 mx12 my12 w180'>
                <div class='col col--12'>
                    <label>Inference Type</label>
                    <div class='select-container w-full'>
                        <select v-model='inf' class='select select--s'>
                            <template v-for='inf in tilejson.inferences'>
                                <option v-bind:key='inf' v-text='inf'></option>
                            </template>
                        </select>
                        <div class='select-arrow'></div>
                    </div>
                </div>
                <div class='col col--12 clearfix pt6'>
                    <button @click='bboxzoom' class='btn round btn--stroke fl btn--gray'><svg class='icon'><use xlink:href='#icon-viewport'/></svg></button>
                </div>
            </div>

            <div class='bg-white round absolute top right z5 mx12 my12'>
                <button @click='fullscreen' class='btn btn--stroke round btn--gray'>
                    <svg class='icon'><use xlink:href='#icon-fullscreen'/></svg>
                </button>
            </div>

            <div id="map" class='w-full h-full'></div>
        </div>
    </div>
</template>

<script>
import buffer from '../../node_modules/@turf/buffer/index.js';
import bboxPolygon from '../../node_modules/@turf/bbox-polygon/index.js';

export default {
    name: 'Map',
    props: ['prediction', 'tilejson'],
    data: function() {
        return {
            inf: false,
            inspect: false,
            opacity: 0.5,
            map: false
        };
    },
    watch: {
        inf: function() {
            for (const inf of this.tilejson.inferences) {
                this.map.setLayoutProperty(`inf-${inf}`, 'visibility', 'none');
            }

            this.map.setLayoutProperty(`inf-${this.inf}`, 'visibility', 'visible');
        }
    },
    mounted: function() {
        this.$nextTick(() => {
            this.init();
        });
    },
    methods: {
        init: function() {
            mapboxgl.accessToken = this.tilejson.token;

            this.map = new mapboxgl.Map({
                container: 'map',
                bounds: this.tilejson.bounds,
                style: 'mapbox://styles/mapbox/satellite-streets-v11'
            });
            this.map.addControl(new mapboxgl.NavigationControl(), 'bottom-right');

            const polyouter = buffer(bboxPolygon(this.tilejson.bounds), 0.3);
            const polyinner = buffer(bboxPolygon(this.tilejson.bounds), 0.1);

            const poly = {
                type: 'Feature',
                properties: {},
                geometry: {
                    type: 'Polygon',
                    coordinates: [
                        polyouter.geometry.coordinates[0],
                        polyinner.geometry.coordinates[0]
                    ]
                }
            };

            this.map.on('load', () => {
                this.map.addSource('tiles', {
                    type: 'vector',
                    tiles: this.tilejson.tiles,
                    minzoom: this.tilejson.minzoom,
                    maxzoom: this.tilejson.maxzoom
                });

                this.map.addSource('bbox', {
                    type: 'geojson',
                    data: poly
                });

                this.map.addLayer({
                    'id': `bbox-layer`,
                    'type': 'fill',
                    'source': 'bbox',
                    'paint': {
                        'fill-color': '#ffffff',
                        'fill-opacity': 1
                    }
                });

                for (const inf of this.tilejson.inferences) {
                    this.map.addLayer({
                        id: `inf-${inf}`,
                        type: 'fill',
                        source: 'tiles',
                        'source-layer': 'data',
                        paint: {
                            'fill-color': '#ff0000',
                            'fill-opacity': [
                                'number',
                                [ '*', ['get', inf], this.opacity ]
                            ]
                        }
                    });
                }

                this.inf = this.tilejson.inferences[0];
            });
        },
        bboxzoom: function() {
            this.map.fitBounds([
                [this.tilejson.bounds[0], this.tilejson.bounds[1]],
                [this.tilejson.bounds[2], this.tilejson.bounds[3]]
            ]);
        },
        fullscreen: function() {
            const container = document.querySelector('#map-container');

            if (!document.fullscreen) {
                 container.requestFullscreen();
            } else {
                document.exitFullscreen();
            }
        }
    }
}
</script>
