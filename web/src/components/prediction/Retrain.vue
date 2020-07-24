<template>
    <div class='col col--12'>
        <div class='col col--12 border-b border--gray-light clearfix mb6'>
            <PredictionHeader
                v-on:mode='mode = $event'
            />
        </div>
        <template v-if='!prediction || loading.imagery'>
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
        <template v-else-if='!imagery || !imagery.length'>
            <div class='flex-parent flex-parent--center-main py12'>
                No imagery sources found to create a stack with
            </div>
        </template>
        <template v-else>
            <div class='col col--12'>
                <label>Imagery Source:</label>
                <div class='border border--gray-light round my12'>
                    <div @click='params.image = img' :key='img.id' v-for='img in imagery' class='col col--12 cursor-pointer bg-darken10-on-hover'>
                        <h3 v-if='params.image.id === img.id' class='px12 py6 txt-h4 w-full bg-gray color-white round' v-text='img.name'></h3>
                        <h3 v-else class='txt-h4 round px12 py6' v-text='img.name'></h3>
                    </div>
                </div>
            </div>
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
        return {
            imagery: [],
            params: {
                image: false,
            },
            loading: {
                imagery: true
            }
        }
    },
    components: {
        UploadPrediction,
        PredictionHeader
    },
    mounted: function() {
        this.getImagery();
    },
    methods: {
        external: function(url) {
            if (!url) return;

            window.open(url, "_blank")
        },
        getImagery: function() {
            this.loading.imagery = true;
            fetch(window.api + `/v1/model/${this.$route.params.modelid}/imagery`, {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((res) => {
                this.imagery = res;

                this.loading.imagery = false;
                if (this.imagery.length === 1) {
                    this.params.image = this.imagery[0];
                }
            }).catch((err) => {
                alert(err);
            });
        },
    }
}
</script>
