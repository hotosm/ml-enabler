<template>
    <div class="col col--12 relative">
        <div class='bg-white round absolute top right z5 mx6 my6'>
            <button @click='fullscreen' class='btn btn--stroke round btn--gray'>
                <svg class='icon'><use xlink:href='#icon-fullscreen'/></svg>
            </button>
        </div>

        <div id="map" class='w-full h600'></div>
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
            map: false
        };
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
            this.map.addControl(new mapboxgl.NavigationControl(), 'top-left');

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
                this.map.addSource('tiles', this.tilejson);
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

            });
        },
        fullscreen: function() {

        }
    }
}
</script>
