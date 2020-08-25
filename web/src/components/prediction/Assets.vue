<template>
    <div class='col col--12'>
        <div class='col col--12 border-b border--gray-light clearfix mb6'>
            <PredictionHeader
                v-on:mode='mode = $event'
            />

            <div class='fr'>
                <button v-if='prediction.logLink' @click='logLink(prediction.logLink)' class='mx3 btn btn--s btn--stroke color-gray color-blue-on-hover round'><svg class='icon fl' style='margin-top: 4px;'><use href='#icon-link'/></svg>Build Log</button>
                <button v-if='prediction.dockerLink' @click='ecrLink(prediction.dockerLink)' class='mx3 btn btn--s btn--stroke color-gray color-blue-on-hover round'><svg class='icon fl' style='margin-top: 4px;'><use href='#icon-link'/></svg> ECR</button>
            </div>
        </div>

        <h2 class='w-full align-center txt-h4 py12'>Prediction Assets</h2>

        <template v-if='prediction.modelLink'>
            <div class='col col--12 py3'>
                <div class='align-center'>TF Model</div>
                <pre class='pre' v-text='"s3://" + prediction.modelLink'></pre>
            </div>
            <div v-if='prediction.tfrecordLink' class='col col--12 py3'>
                <div class='align-center'>TF Records</div>
                <pre class='pre' v-text='"s3://" + prediction.tfrecordLink'></pre>
            </div>
            <div v-if='prediction.checkpointLink' class='col col--12 py3'>
                <div class='align-center'>TF Checkpoint</div>
                <pre class='pre' v-text='"s3://" + prediction.checkpointLink'></pre>
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

            <UploadPrediction
                type='model'
                :prediction='prediction'
                v-on:close='$router.push({ name: "model", params: { modelid: $route.params.modelid } })'
            />
        </template>
    </div>
</template>

<script>
import UploadPrediction from './UploadPrediction.vue';
import PredictionHeader from './PredictionHeader.vue';

export default {
    name: 'Assets',
    props: ['meta', 'prediction'],
    data: function() {
        return { }
    },
    components: {
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
        }
    }
}
</script>
