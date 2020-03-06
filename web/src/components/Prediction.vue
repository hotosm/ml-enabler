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

            </template>
            <template v-else>
                <div class='align-center pb6'>Upload a model to get started</div>

                <UploadPrediction :prediction='prediction'/>
            </template>
        </div>
    </div>
</template>

<script>
import UploadPrediction from './UploadPrediction.vue';

export default {
    name: 'Prediction',
    props: ['model', 'prediction'],
    data: function() {
        return {
            mode: 'prediction'
        }
    },
    components: {
        UploadPrediction
    },
    methods: {
        close: function() {
            this.$emit('close');
        },
        external: function(url) {
            if (!url) return;

            window.open(url, "_blank")
        }
    }
}
</script>
