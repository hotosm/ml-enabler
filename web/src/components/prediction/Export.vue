<template>
    <div class='col col--12 relative'>
        <div class='col col--12 border-b border--gray-light clearfix mb6'>
            <PredictionHeader/>
        </div>

        <template v-if='tilejson'>
            <div class='col col--12 grid grid--gut12'>
                <div class='col col--6'>
                    <h2 class='txt-h4 py12'>Export Inferences</h2>
                </div>
                <div class='col col--6'>
                    <div class="flex-parent-inline fr py12">
                        <button @click='mode = "download"' :class='{
                            "btn--stroke": mode !== "download"
                        }' class="btn btn--pill btn--pill-stroke btn--s btn--pill-hl round">Download</button>
                        <button @click='mode = "integrations"' :class='{
                            "btn--stroke": mode !== "integrations"
                        }' class="btn btn--pill btn--s btn--pill-hr btn--pill-stroke round">Integrations</button>
                    </div>
                </div>

                <template v-if='mode === "download"'>
                    <div class='col col--6'>
                        <label>Type</label>
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
                </template>
                <template v-else-if='mode === "integrations"'>
                    <template v-if='!integration'>
                        <Integrations @integration='integration = $event'/>
                    </template>
                    <template v-else>
                        <div class='col col--12 ml12 mb3'>
                            <h2 class='txt-h4 fl' v-text='integration.name'></h2>

                            <button @click='integration = false' class='btn fr round btn--stroke color-gray color-black-on-hover'>
                                <svg class='icon'><use href='#icon-close'/></svg>
                            </button>
                        </div>
                        <div class='grid grid--gut12 col col--12 border border--gray-light round ml12'>
                            <div class='col col--12 pt12 pr12'>
                                <label>Project Name</label>
                                <input type='text' v-model='mr.project' class='input'/>
                            </div>
                            <div class='col col--12 pt12 pr12'>
                                <label>Project Description</label>
                                <textarea v-model='project_desc' class='textarea'></textarea>
                            </div>
                            <div class='col col--12 pt12 pr12'>
                                <label>Challenge Name</label>
                                <input type='text' v-model='mr.challenge' class='input'/>
                            </div>
                            <div class='col col--12 pt12 pr12'>
                                <label>Challenge Instructions</label>
                                <textarea v-model='challenge_instr' class='textarea'></textarea>
                            </div>
                            <div class='col col--6 py12'>
                                <label>Threshold (<span v-text='mr.threshold'/>%)</label>
                                <div class='range range--s color-gray'>
                                    <input :disabled='mr.inferences === "all"' v-on:input='mr.threshold = parseInt($event.target.value)' type='range' min=0 max=100 />
                                </div>
                            </div>

                            <div class='col col--6 py12 pr12'>
                                <label>Inferences</label>
                                <div class='select-container w-full'>
                                    <select v-model='mr.inferences' class='select'>
                                        <option value='all'>All</option>
                                        <option :key='inf' v-for='inf in tilejson.inferences' :value='inf'><span v-text='inf'/></option>
                                    </select>
                                    <div class='select-arrow'></div>
                                </div>
                            </div>
                            <div class='col col--12 clearfix pt6 pb12 pr12'>
                                <button @click='getExport' class='fr btn btn--stroke color-gray color-green-on-hover round'>Submit</button>
                            </div>
                            </div>
                    </template>
                </template>
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
import Integrations from '../Integrations.vue';

export default {
    name: 'Export',
    props: ['meta', 'tilejson', 'model', 'prediction'],
    data: function() {
        return {
            mode: 'download',
            loading: false,
            integration: false,
            mr: {
                project: '',
                project_desc: '',
                challenge: '',
                challenge_instr: '',
                format: 'geojson',
                inferences: 'all',
                threshold: 50
            },
            params: {
                format: 'geojson',
                inferences: 'all',
                threshold: 50
            }
        };
    },
    mounted: function() {
        this.mr.project = this.model.name;
        this.mr.challenge = 'v' + this.prediction.version;
    },
    methods: {
        getExport: function() {
            const url = new URL(`${window.api}/v1/model/${this.$route.params.modelid}/prediction/${this.$route.params.predid}/export`);

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
        PredictionHeader,
        Integrations
    }
}
</script>
