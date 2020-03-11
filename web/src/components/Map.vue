<template>
    <div class="col col--12">
        <div id="map"></div>
    </div>
</template>

<script>
export default {
    name: 'Map',
    props: ['prediction', 'tilejson'],
    data: function() {
        return {
            map: false
        };
    },
    mounted: function() {
        this.$nexttick(() => {
            this.init();
        });
    },
    methods: {
        init: function() {
            mapboxgl.accessToken = this.tilejson.token;

            this.map = new mapboxgl.Map({
                container: 'map',
                style: 'mapbox://styles/mapbox/streets-v9'
            });
        }
    }
}
</script>
