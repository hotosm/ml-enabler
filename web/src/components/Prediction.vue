<template>
    <div class="col col--12">
        <div class='col col--12 clearfix py6'>
            <h2 class='fl cursor-default' v-text='"Prediction: " + prediction.version'></h2>

            <button @click='$router.push({ name: "model", params: { modelid: $route.params.modelid } })' class='btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-close'/></svg>
            </button>

            <span class='fr mr6 bg-blue-faint bg-blue-on-hover color-white-on-hover color-blue inline-block px6 py3 round txt-xs txt-bold cursor-pointer' v-text='"id: " + prediction.predictionsId'/>
        </div>
        <div class='border border--gray-light round col col--12 px12 py12 clearfix'>
            <template v-if='mode === "assets"'>
                <div class='col col--12 border-b border--gray-light clearfix mb6'>
                    <PredictionHeader
                        :mode='mode'
                        v-on:mode='mode = $event'
                    />

                    <div class='fr'>
                        <button v-if='prediction.logLink' @click='logLink(prediction.logLink)' class='mx3 btn btn--s btn--stroke color-gray color-blue-on-hover round'><svg class='icon fl' style='margin-top: 4px;'><use href='#icon-link'/></svg>Build Log</button>
                        <button v-if='prediction.dockerLink' @click='ecrLink(prediction.dockerLink)' class='mx3 btn btn--s btn--stroke color-gray color-blue-on-hover round'><svg class='icon fl' style='margin-top: 4px;'><use href='#icon-link'/></svg> ECR</button>
                    </div>
                </div>
                <template v-if='prediction.modelLink'>
                    <div class='col col--12 py3'>
                        <div class='align-center'>TF Model</div>
                        <pre class='pre' v-text='"s3://" + prediction.modelLink'></pre>
                    </div>
                    <div v-if='prediction.saveLink' class='col col--12 py3'>
                        <div class='align-center'>TFServing Container</div>
                        <pre class='pre' v-text='"s3://" + prediction.saveLink'></pre>
                    </div>
                    <div v-if='prediction.saveLink' class='col col--12 py3'>
                        <div class='align-center'>ECR Container</div>
                        <pre class='pre' v-text='prediction.dockerLink'></pre>
                    </div>
                </template>
                <template v-else-if='meta.environment !== "aws"'>
                    <div class='flex-parent flex-parent--center-main pt36'>
                        <svg class='flex-child icon w60 h60 color--gray'><use href='#icon-info'/></svg>
                    </div>

                    <div class='flex-parent flex-parent--center-main pt12 pb36'>
                        <h1 class='flex-child txt-h4 cursor-default align-center'>Assets can only be created when MLEnabler is running in an "aws" environment</h1>
                    </div>
                </template>
                <template v-else>
                    <div class='align-center pb6'>Upload a model to get started</div>

                    <UploadPrediction :prediction='prediction' v-on:close='$router.push({ name: "model", params: { modelid: $route.params.modelid } })'/>
                </template>
            </template>
            <template v-else-if='mode === "stack"'>
                <Stack
                    :meta='meta'
                    :prediction='prediction'
                    v-on:mode='mode = $event'
                />
            </template>
            <template v-else-if='mode === "map"'>
                <div class='col col--12 border-b border--gray-light clearfix mb6'>
                    <PredictionHeader
                        :mode='mode'
                        v-on:mode='mode = $event'
                    />

                    <div class='fr'>
                        <button @click='refresh' class='mx3 btn btn--stroke color-gray color-blue-on-hover round'><svg class='icon fl'><use href='#icon-refresh'/></svg></button>
                    </div>
                </div>
                <template v-if='tiles'>
                    <div class='align-center pb6'>Prediction Tiles</div>

                    <Map :prediction='prediction' :tilejson='tiles'/>
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
            </template>
            <template v-else-if='mode === "export"'>
                <Export
                    :meta='meta'
                    :prediction='prediction'
                    :tilejson='tiles'
                    v-on:mode='mode = $event'
                />
            </template>
        </div>
    </div>
</template>

<script>
import UploadPrediction from './prediction/UploadPrediction.vue';
import PredictionHeader from './PredictionHeader.vue';
import Export from './prediction/Export.vue';
import Stack from './prediction/Stack.vue';
import Map from './prediction/Map.vue';

export default {
    name: 'Prediction',
    props: ['meta'],
    data: function() {
        return {
            mode: 'assets',
            prediction: {},
            tiles: false
        }
    },
    mounted: function() {
        this.refresh();
    },
    components: {
        Map,
        Stack,
        Export,
        PredictionHeader,
        UploadPrediction
    },
    methods: {
        ecrLink(ecr) {
            const url = `https://console.aws.amazon.com/ecr/repositories/${ecr.split(':')[0]}/`;
            this.external(url);
        },
        logLink: function(stream) {
            const url = `https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/%252Faws%252Fbatch%252Fjob/log-events/${encodeURIComponent(stream)}`
            this.external(url);
        },
        external: function(url) {
            if (!url) return;

            window.open(url, "_blank")
        },
        refresh: function() {
            this.getTilejson();
            this.getPrediction();
        },
        getPrediction: function() {
            fetch(window.api + `/v1/model/${this.$route.params.modelid}/prediction/${this.$route.params.predid}`, {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((res) => {
                this.prediction = res;
            });
        },
        getTilejson: function() {
            fetch(window.api + `/v1/model/${this.$route.params.modelid}/prediction/${this.$route.params.predid}/tiles`, {
                method: 'GET',
                credentials: 'same-origin'
            }).then((res) => {
                if (res.status === 404) {
                    this.tiles = false;
                } else {
                    res.json().then((tilejson) => {
                        tilejson.tiles[0] = window.location.origin + window.api + tilejson.tiles[0];

                        this.tiles = tilejson;
                    })
                }
            });
        }
    }
}
</script>
