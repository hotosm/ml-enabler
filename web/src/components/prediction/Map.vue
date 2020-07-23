<template>
    <div class='col col--12'>
        <div class='col col--12 border-b border--gray-light clearfix mb6'>
            <PredictionHeader/>

            <div class='fr'>
                <button @click='$emit("refresh")' class='mx3 btn btn--stroke color-gray color-blue-on-hover round'><svg class='icon fl'><use href='#icon-refresh'/></svg></button>
            </div>
        </div>

        <template v-if='tilejson'>
            <div class='align-center pb6'>Prediction Tiles</div>

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

                        <template v-if='!advanced'>
                            <div class='col col--12'>
                                <button @click='advanced = !advanced' class='btn btn--white color-gray px0'><svg class='icon fl my6'><use xlink:href='#icon-chevron-right'/></svg><span class='fl pl6'>Advanced Options</span></button>
                            </div>
                        </template>
                        <template v-else>
                            <div class='col col--12 border-b border--gray-light mb12'>
                                <button @click='advanced = !advanced' class='btn btn--white color-gray px0'><svg class='icon fl my6'><use xlink:href='#icon-chevron-down'/></svg><span class='fl pl6'>Advanced Options</span></button>
                            </div>
                        </template>

                        <template v-if='advanced'>
                            <div class='col col--12'>
                                <label>Opacity (<span v-text='opacity'/>%)</label>
                                <div class='range range--s color-gray'>
                                    <input v-on:input='opacity = parseInt($event.target.value)' type='range' min=0 max=100 />
                                </div>
                            </div>

                            <div class='col col--12'>
                                <label>Threshold (<span v-text='threshold'/>%)</label>
                                <div class='range range--s color-gray'>
                                    <input v-on:input='threshold = parseInt($event.target.value)' type='range' min=0 max=100 />
                                </div>
                            </div>

                            <div class='col col--12'>
                                <label>Imagery</label>
                                <div class='select-container w-full'>
                                    <select v-model='bg' class='select select--s'>
                                        <option value='default'>Default</option>
                                        <option v-for='img in imagery' v-bind:key='img.id' :value='img.id' v-text='img.name'></option>
                                    </select>
                                    <div class='select-arrow'></div>
                                </div>
                            </div>
                        </template>
                    </div>

                    <div class='bg-white round absolute top right z5 mx12 my12'>
                        <button @click='fullscreen' class='btn btn--stroke round btn--gray'>
                            <svg class='icon'><use xlink:href='#icon-fullscreen'/></svg>
                        </button>
                    </div>

                    <div class='absolute z5 w180 bg-white round px12 py12' style='bottom: 40px; left: 12px;'>
                        <template v-if='inspect'>
                            <div class='flex-parent flex-parent--center-main'>
                                <div class='flex-child'>
                                    <svg class='icon w30 h30'><use xlink:href='#icon-info'/></svg>
                                </div>
                            </div>
                            <div class='flex-parent flex-parent--center-main'>
                                <div class='flex-child'>
                                    <span v-text='inf'></span>: <span v-text='(inspect * 100).toFixed(1)'></span>%
                                </div>
                            </div>
                        </template>
                        <template v-else>
                            <div class='flex-parent flex-parent--center-main'>
                                <div class='flex-child'>
                                    <svg class='icon w30 h30'><use xlink:href='#icon-cursor'/></svg>
                                </div>
                            </div>
                            <div class='flex-parent flex-parent--center-main'>
                                <div class='flex-child'>
                                    <div align=center>Hover for Details</div>
                                </div>
                            </div>
                        </template>
                    </div>

                    <div id="map" class='w-full h-full'></div>
                </div>
            </div>
        </template>
        <template v-else>
            <div class='col col--12 py6'>
                <div class='flex-parent flex-parent--center-main pt36'>
                    <svg class='flex-child icon w60 h60 color-gray'><use href='#icon-info'/></svg>
                </div>

                <div class='flex-parent flex-parent--center-main pt12 pb36'>
                    <h1 class='flex-child txt-h4 cursor-default'>No Inferences Uploaded</h1>
                </div>
            </div>
        </template>
    </div>
</template>

<script>
import buffer from '../../../node_modules/@turf/buffer/index.js';
import bboxPolygon from '../../../node_modules/@turf/bbox-polygon/index.js';
import PredictionHeader from './PredictionHeader.vue';

export default {
    name: 'Map',
    props: ['meta', 'prediction', 'tilejson'],
    data: function() {
        return {
            popup: false,
            popupid: false,
            bg: 'default',
            inf: false,
            inspect: false,
            advanced: false,
            threshold: 50,
            opacity: 50,
            map: false,
            imagery: []
        };
    },
    watch: {
        bg: function() {
            this.layers();
        },
        tilejson: function() {
            if (this.map) this.map.remove();
            if (this.tilejson) {
                this.$nextTick(() => {
                    this.init();
                });
            }
        },
        opacity: function() {
            for (const inf of this.tilejson.inferences) {
                this.map.setPaintProperty(
                    `inf-${inf}`,
                    'fill-opacity',
                    [ 'number', [ '*', ['get', inf], (this.opacity / 100) ] ]
                );
            }
        },
        threshold: function() {
            for (const inf of this.tilejson.inferences) {
                this.filter(inf);
            }
        },
        inf: function() {
            this.hide();
        }
    },
    mounted: function() {
        this.getImagery();

        if (this.tilejson) {
            this.$nextTick(() => {
                this.init();
            });
        }
    },
    methods: {
        infValidity: function(id, valid) {
            this.popup.remove();

            const prop = {};
            prop[`v_${this.inf}`] = valid;
            this.map.setFeatureState({
                id: id,
                source: 'tiles',
                sourceLayer: 'data'
            }, prop);

            const body = {
                id: id,
                validity: {}
            };

            body.validity[this.inf] = valid;

            fetch(window.api + `/v1/model/${this.$route.params.modelid}/prediction/${this.$route.params.predid}/validity`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(body)
            }).then((res) => {
                return res.json();
            }).then(() => {

            }).catch((err) => {
                alert(err);
            });
        },
        hide: function() {
            for (const inf of this.tilejson.inferences) {
                this.map.setLayoutProperty(`inf-${inf}`, 'visibility', 'none');
            }

            this.map.setLayoutProperty(`inf-${this.inf}`, 'visibility', 'visible');
        },
        init: function() {
            mapboxgl.accessToken = this.tilejson.token;

            this.map = new mapboxgl.Map({
                container: 'map',
                bounds: this.tilejson.bounds,
                style: 'mapbox://styles/mapbox/satellite-streets-v11'
            });

            this.map.addControl(new mapboxgl.NavigationControl(), 'bottom-right');

            this.map.on('load', () => {
                this.styles();
            });
        },
        layers: function() {
            this.map.once('styledata', () => {
                this.styles();
            });

            if (this.bg === 'default') {
                this.map.setStyle('mapbox://styles/mapbox/satellite-streets-v11', {
                    diff: false
                });
            } else {
                for (const img of this.imagery) {
                    if (img.id === this.bg) {
                        this.map.setStyle({
                            version: 8,
                            sources: {
                                'raster-tiles': {
                                    type: 'raster',
                                    tiles: [ img.url ]
                                }
                            },
                            layers:  [{
                                id: 'simple-tiles',
                                type: 'raster',
                                source: 'raster-tiles',
                                minzoom: 0,
                                maxzoom: 22
                            }]
                        }, {
                            diff: false
                        });
                        break;
                    }
                }
            }
        },
        bboxzoom: function() {
            this.map.fitBounds([
                [this.tilejson.bounds[0], this.tilejson.bounds[1]],
                [this.tilejson.bounds[2], this.tilejson.bounds[3]]
            ]);
        },
        filter: function(inf) {
            this.map.setFilter(`inf-${inf}`, ['>=', inf, this.threshold / 100]);
        },
        styles: function() {
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

            if (!this.map.getSource('tiles')) {
                this.map.addSource('tiles', {
                    type: 'vector',
                    tiles: this.tilejson.tiles,
                    minzoom: this.tilejson.minzoom,
                    maxzoom: this.tilejson.maxzoom
                });
            }

            if (!this.map.getSource('bbox')) {
                this.map.addSource('bbox', {
                    type: 'geojson',
                    data: poly
                });
            }

            if (!this.map.getLayer('bbox-layer')) {
                this.map.addLayer({
                    'id': `bbox-layer`,
                    'type': 'fill',
                    'source': 'bbox',
                    'paint': {
                        'fill-color': '#ffffff',
                        'fill-opacity': 1
                    }
                });
            }

            for (const inf of this.tilejson.inferences) {
                this.map.addLayer({
                    id: `inf-${inf}`,
                    type: 'fill',
                    source: 'tiles',
                    'source-layer': 'data',
                    paint: {
                        'fill-color': [
                            'case',
                            ['==', ["feature-state", `v_${inf}`], false], '#ffffff',
                            ['==', ["feature-state", `v_${inf}`], true], '#00ff00',
                            ['==', ['get', `v_${inf}`], false], '#ffffff',
                            ['==', ['get', `v_${inf}`], true], '#00ff00',
                            '#ff0000'
                        ],
                        'fill-opacity': [
                            'number',
                            [ '*', ['get', inf], (this.opacity / 100) ]
                        ]
                    }
                });

                this.filter(inf);

                this.map.on('click', `inf-${inf}`, (e) => {
                    if (
                        e.features.length === 0
                        || !e.features[0].properties[this.inf]
                        || e.features[0].properties[this.inf] === 0
                    ) return;

                    this.popupid = e.features[0].id;

                    this.popup = new mapboxgl.Popup({
                        className: 'infpop'
                    })
                        .setLngLat(e.lngLat)
                        .setHTML(`
                            <div class='col col--12'>
                                <h1 class="txt-h5 mb3 align-center">Inf Geom</h1>
                                <button id="valid" class="w-full round btn btn--gray color-green-on-hover btn--s btn--stroke mb6">Valid</button>
                                <button id="invalid" class="w-full round btn btn--gray color-red-on-hover btn--s btn--stroke">Invalid</button>
                            </div>
                        `)
                        .setMaxWidth("200px")
                        .addTo(this.map);

                    this.$nextTick(() => {
                        document.querySelector('#valid').addEventListener('click', () => {
                            this.infValidity(this.popupid, true)
                        });
                        document.querySelector('#invalid').addEventListener('click', () => {
                            this.infValidity(this.popupid, false)
                        });
                    });
                });

                this.map.on('mousemove', `inf-${inf}`, (e) => {
                    if (
                        e.features.length === 0
                        || !e.features[0].properties[this.inf]
                        || e.features[0].properties[this.inf] === 0
                    ) {
                        this.map.getCanvas().style.cursor = '';
                        this.inspect = false;
                        return;
                    }

                    this.map.getCanvas().style.cursor = 'pointer';

                    this.inspect = e.features[0].properties[this.inf];
                });
            }

            this.inf = this.tilejson.inferences[0];
            this.hide();
        },
        fullscreen: function() {
            const container = document.querySelector('#map-container');

            if (!document.fullscreen) {
                 container.requestFullscreen();
            } else {
                document.exitFullscreen();
            }
        },
        getImagery: function() {
            fetch(window.api + `/v1/model/${this.$route.params.modelid}/imagery`, {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((res) => {
                this.imagery = res;
            }).catch((err) => {
                alert(err);
            });
        },
    },
    components: {
        PredictionHeader
    }
}
</script>
