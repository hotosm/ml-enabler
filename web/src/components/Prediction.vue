<template>
    <div class="col col--12">
        <div class='col col--12 clearfix py6'>
            <h2 class='fl cursor-default' v-text='"Prediction: " + prediction.versionString'></h2>

            <button @click='close' class='btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-close'/></svg>
            </button>
        </div>
        <div class='border border--gray-light round col col--12 px12 py12 clearfix'>
            <template v-if='prediction.modelLink'>
                <div class='col col--12 border-b border--gray-light clearfix mb6'>
                    <h3 class='fl mt6 cursor-default'>Assets:</h3>

                    <button v-if='prediction.logLink' @click='logLink(prediction.logLink)' class='fr btn btn--s btn--stroke color-gray color-blue-on-hover round ml6'><svg class='icon fl' style='margin-top: 4px;'><use href='#icon-link'/></svg>Build Log</button>
                    <button v-if='prediction.dockerLink' @click='ecrLink(prediction.dockerLink)' class='fr btn btn--s btn--stroke color-gray color-blue-on-hover round mx6'><svg class='icon fl' style='margin-top: 4px;'><use href='#icon-link'/></svg> ECR</button>
                </div>

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

            <template v-if='tiles'>
                <div class='align-center pb6'>Prediction Tiles</div>

                <Map :prediction='prediction' :tilejson='tilejson'/>
            </template>
        </div>
    </div>
</template>

<script>
import UploadPrediction from './UploadPrediction.vue';
import Map from './Map.vue';

export default {
    name: 'Prediction',
    props: ['model', 'prediction'],
    data: function() {
        return {
            mode: 'prediction',
            tiles: false
        }
    },
    mounted: function() {
        this.getTilejson();
    },
    components: {
        Map,
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
            fetch(`${window.location.origin}/v1/model/${this.model.modelId}/prediction/${this.prediction.predictionId}/tiles`, {
                method: 'GET',
                credentials: 'same-origin'
            }).then((res) => {
                if (res.status === 404) {
                    this.tiles = false;
                } else {
                    return res.json();
                }
            }).then((tilejson) => {
                this.tiles = tilejson;
            });
        }
    }
}
</script>
