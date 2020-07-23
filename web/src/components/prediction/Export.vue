<template>
    <div class='col col--12 relative'>
        <div class='col col--12 border-b border--gray-light clearfix mb6'>
            <PredictionHeader/>
        </div>

        <template v-if='tilejson'>
            <div class='col col--12 grid grid--gut12'>
                <h2 class='w-full align-center txt-h4 py12'>Export Inferences</h2>

                <div class='col col--6'>
                    <label>Format</label>
                    <div class='select-container w-full'>
                        <select v-model='params.format' class='select'>
                            <option value='geojson'>GeoJSON</option>
                            <option value='geojsonld'>GeoJSON LD</option>
                            <option value='csv'>CSV</option>
                            <option value='npz'>NPZ</option>
                        </select>
                        <div class='select-arrow'></div>
                    </div>
                </div>
                <div class='col col--6'>
                    <label>Inferences</label>
                    <div class='select-container w-full'>
                        <select v-model='params.inferences' class='select'>
                            <option value='all'>All</option>
                            <option :key='inf' v-for='inf in tilejson.inferences' :value='inf'><span v-text='inf'/></option>
                        </select>
                        <div class='select-arrow'></div>
                    </div>
                </div>
                <div class='col col--12 py12'>
                    <label>Threshold (<span v-text='params.threshold'/>%)</label>
                    <div class='range range--s color-gray'>
                        <input :disabled='params.inferences === "all"' v-on:input='params.threshold = parseInt($event.target.value)' type='range' min=0 max=100 />
                    </div>
                </div>

                <div class='col col--12 clearfix py6'>
                    <button @click='getExport' class='fr btn btn--stroke color-gray color-green-on-hover round'>Export</button>
                </div>
            </div>
        </template>
        <template v-else-if='loading'>
            <div class='flex-parent flex-parent--center-main w-full py24'>
                <div class='flex-child loading py24'></div>
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
import PredictionHeader from './PredictionHeader.vue';

export default {
    name: 'Export',
    props: ['meta', 'tilejson'],
    data: function() {
        return {
            loading: false,
            params: {
                format: 'geojson',
                inferences: 'all',
                threshold: 50
            }
        };
    },
    methods: {
        getExport: function() {
            const url = new URL(`${window.location.origin}${window.api}/v1/model/${this.$route.params.modelid}/prediction/${this.$route.params.predid}/export`);

            url.searchParams.set('format', this.params.format);
            url.searchParams.set('inferences', this.params.inferences);

            if (this.params.inferences !== 'all') {
                url.searchParams.set('threshold', this.params.threshold / 100);
            }

            this.external(url);
        },
        external: function(url) {
            if (!url) return;

            window.open(url, "_blank")
        },
    },
    components: {
        PredictionHeader
    }
}
</script>
