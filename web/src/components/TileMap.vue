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
import bboxPolygon from '../../node_modules/@turf/bbox-polygon/index.js';

export default {
    name: 'TileMap',
    props: ['tilejson'],
    data: function() {
        return {
            map: false,
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
        this.init();
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
            mapboxgl.accessToken = this.tilejson.token;

            this.map = new mapboxgl.Map({
                container: 'map',
                zoom: 1,
                style: 'mapbox://styles/mapbox/satellite-streets-v11'
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
