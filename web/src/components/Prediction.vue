<template>
    <div class="col col--12">
        <div class='col col--12 clearfix py6'>
            <h2 class='fl cursor-default' v-text='"Prediction: " + prediction.versionString'></h2>

            <button @click='close' class='btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-close'/></svg>
            </button>

            <span class='fr mr6 bg-blue-faint bg-blue-on-hover color-white-on-hover color-blue inline-block px6 py3 round txt-xs txt-bold cursor-pointer' v-text='"id: " + prediction.predictionsId'/>
        </div>
        <div class='border border--gray-light round col col--12 px12 py12 clearfix'>
            <div class='col col--12 border-b border--gray-light clearfix mb6'>
                <div class="flex-parent-inline py3">
                    <button @click='mode = "assets"' class="btn btn--pill btn--s btn--pill-hl round">Assets</button>
                    <button @click='mode = "stack"' class="btn btn--pill btn--s btn--pill-hc round">Stack</button>
                    <button @click='mode = "map"' class="btn btn--pill btn--s btn--pill-hr round">Map</button>
                </div>

                <div v-if='mode === "assets"' class="flex-parent-inline py3 fr">
                    <button v-if='prediction.logLink' @click='logLink(prediction.logLink)' class='mr6 btn btn--s btn--stroke color-gray color-blue-on-hover round'><svg class='icon fl' style='margin-top: 4px;'><use href='#icon-link'/></svg>Build Log</button>
                    <button v-if='prediction.dockerLink' @click='ecrLink(prediction.dockerLink)' class='btn btn--s btn--stroke color-gray color-blue-on-hover round'><svg class='icon fl' style='margin-top: 4px;'><use href='#icon-link'/></svg> ECR</button>
                </div>
            </div>

            <template v-if='mode === "assets"'>
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
                <template v-else>
                        <div class='align-center pb6'>Upload a model to get started</div>

                        <UploadPrediction :prediction='prediction' v-on:close='close'/>
                </template>
            </template>
            <template v-else-if='mode === "stack"'>
                <template v-if='!prediction.modelLink'>
                    <div class='col col--12 py6'>
                        <div class='flex-parent flex-parent--center-main pt36'>
                            <svg class='flex-child icon w60 h60 color--gray'><use href='#icon-info'/></svg>
                        </div>

                        <div class='flex-parent flex-parent--center-main pt12 pb36'>
                            <h1 class='flex-child txt-h4 cursor-default'>A Model must be uploaded before a stack is created</h1>
                        </div>
                    </div>
                </template>
                <template v-else>
                    <Stack
                        :model='model'
                        :tilejson='tiles'
                        :prediction='prediction'
                    />
                </template>
            </template>
            <template v-else-if='mode === "map"'>
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
        </div>
    </div>
</template>

<script>
import UploadPrediction from './UploadPrediction.vue';
import Stack from './Stack.vue';
import Map from './Map.vue';

export default {
    name: 'Prediction',
    props: ['model', 'prediction'],
    data: function() {
        return {
            mode: 'assets',
            tiles: false
        }
    },
    mounted: function() {
        this.getTilejson();
    },
    components: {
        Map,
        Stack,
        UploadPrediction
    },
    methods: {
        close: function() {
            this.$emit('close');
        },
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
        getTilejson: function() {
            fetch(`${window.location.origin}/v1/model/${this.model.modelId}/prediction/${this.prediction.predictionsId}/tiles`, {
                method: 'GET',
                credentials: 'same-origin'
            }).then((res) => {
                if (res.status === 404) {
                    this.tiles = false;
                } else {
                    return res.json();
                }
            }).then((tilejson) => {
                tilejson.tiles[0] = window.location.origin + tilejson.tiles[0];

                this.tiles = tilejson;
            });
        }
    }
}
</script>
