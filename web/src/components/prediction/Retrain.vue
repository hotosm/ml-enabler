<template>
    <div class='col col--12'>
        <div class='col col--12 border-b border--gray-light clearfix mb6'>
            <PredictionHeader
                v-on:mode='mode = $event'
            />
        </div>
        <template v-if='!prediction'>
            <div class='flex-parent flex-parent--center-main w-full py24'>
                <div class='flex-child loading py24'></div>
            </div>
        </template>
        <template v-else-if='meta.environment !== "aws"'>
            <div class='flex-parent flex-parent--center-main pt36'>
                <svg class='flex-child icon w60 h60 color--gray'><use href='#icon-info'/></svg>
            </div>

            <div class='flex-parent flex-parent--center-main pt12 pb36'>
                <h1 class='flex-child txt-h4 cursor-default align-center'>
                    Retraining can only occur when MLEnabler is running in an "aws" environment
                </h1>
            </div>
        </template>
        <template v-else-if='!prediction.modelLink'>
            <div class='flex-parent flex-parent--center-main pt36'>
                <svg class='flex-child icon w60 h60 color--gray'><use href='#icon-info'/></svg>
            </div>

            <div class='flex-parent flex-parent--center-main pt12 pb36'>
                <h1 class='flex-child txt-h4 cursor-default align-center'>
                    A model must be uploaded before retraining occurs
                </h1>
            </div>
            <div class='flex-parent flex-parent--center-main pt12 pb36'>
                <button @click='$router.push({ name: "assets" })' class='flex-child btn btn--stroke round'>
                    Upload Model
                </button>
            </div>
        </template>
        <template v-else-if='!tilejson'>
            <div class='flex-parent flex-parent--center-main pt36'>
                <svg class='flex-child icon w60 h60 color-gray'><use href='#icon-info'/></svg>
            </div>

            <div class='flex-parent flex-parent--center-main pt12 pb36'>
                <h1 class='flex-child txt-h4 cursor-default'>No Inferences Uploaded</h1>
            </div>

            <div class='flex-parent flex-parent--center-main pt12 pb36'>
                <button @click='$router.push({ name: "stack" })' class='flex-child btn btn--stroke round'>
                    Create Inference Stack
                </button>
            </div>
        </template>
        <template v-else-if='!prediction.checkpointLink'>
            <div class='flex-parent flex-parent--center-main pt12 pb36'>
                <h1 class='flex-child txt-h4 cursor-default align-center'>
                    Checkpoint Upload
                </h1>
            </div>
            <UploadPrediction
                type='checkpoint'
                :prediction='prediction'
                v-on:close='$emit("refresh")'
            />
        </template>
    </div>
</template>

<script>
import PredictionHeader from './PredictionHeader.vue';
import UploadPrediction from './UploadPrediction.vue';

export default {
    name: 'Retrain',
    props: ['meta', 'prediction', 'tilejson'],
    data: function() {
        return { }
    },
    components: {
        UploadPrediction,
        PredictionHeader
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
