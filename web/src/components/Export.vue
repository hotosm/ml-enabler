<template>
    <div class='col col--12 relative'>
        <div class='col col--12 border-b border--gray-light clearfix mb6'>
            <PredictionHeader
                mode='export'
                v-on:mode='$emit("mode", $event)'
            />
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
                        </select>
                        <div class='select-arrow'></div>
                    </div>
                </div>
                <div class='col col--6'>
                    <label>Inferences</label>
                    <div class='select-container w-full'>
                        <select v-model='params.inferences' class='select'>
                            <option value='all'>All</option>
                            <template v-for='inf in tilejson.inferences'>
                                <option value='inf'><span v-text='inf'/></option>
                            </template>
                        </select>
                        <div class='select-arrow'></div>
                    </div>
                </div>

                <div class='col col--12 clearfix py6'>
                    <button class='fr btn btn--stroke color-gray color-green-on-hover round'>Export</button>
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
    props: ['meta', 'model', 'prediction', 'tilejson'],
    data: function() {
        return {
            loading: false,
            params: {
                format: 'geojson',
                inferences: 'all'
            }
        };
    },
    components: {
        PredictionHeader
    }
}
</script>
