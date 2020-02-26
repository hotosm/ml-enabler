<template>
    <div class="col col--12">
        <div class='col col--12 clearfix py6'>
            <h2 class='fl cursor-default' v-text='model.name + " - " + model.source'></h2>

            <button @click='close' class='btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-close'/></svg>
            </button>

            <button @click='external(model.projectUrl)' class='mr12 btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-link'/></svg>
            </button>

            <button @click='edit' class='mr12 btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-pencil'/></svg>
            </button>
        </div>
        <div class='border border--gray-light round col col--12 px12 py12 clearfix'>
            <template v-if='mode === "model"'>
                <div class='col col--12 border-b border--gray-light clearfix'>
                    <h3 class='fl mt6 cursor-default'>Predictions:</h3>

                    <button @click='mode = "editprediction"' class='btn fr mb6 round btn--stroke color-gray color-green-on-hover'>
                        <svg class='icon'><use href='#icon-plus'/></svg>
                    </button>
                </div>

                <div class='grid grid--gut12'>
                    <template v-if='predictions.length === 0'>
                        <div class='col col--12 py6'>
                            <div class='flex-parent flex-parent--center-main pt36'>
                                <svg class='flex-child icon w60 h60 color--gray'><use href='#icon-info'/></svg>
                            </div>

                            <div class='flex-parent flex-parent--center-main pt12 pb36'>
                                <h1 class='flex-child txt-h4 cursor-default'>No Predictions Yet</h1>
                            </div>
                        </div>
                    </template>
                    <template v-else>
                        <div :key='pred.predictionsId' v-for='pred in predictions' class='cursor-default col col--12'>
                            <div class='col col--12 grid py6 px12 bg-darken10-on-hover'>
                                <div class='col col--6'>
                                    <div class='col col--12 clearfix'>
                                        <h3 class='txt-h4 fl' v-text='pred.versionString'></h3>
                                    </div>
                                </div>
                                <div class='col col--6'>
                                </div>
                            </div>
                        </div>

                    </template>
                </div>
            </template>
            <template v-else-if='mode="editprediction"'>
                <EditPrediction :prediction='prediction' v-on:close='getPredictions' />
            </template>
        </div>
    </div>
</template>

<script>
import EditPrediction from './EditPrediction.vue';

export default {
    name: 'Model',
    props: ['model'],
    data: function() {
        return {
            mode: 'model',
            predictions: [],
            prediction: {
                modelId: this.model.modelId,
                version: '',
                tileZoom: 18,
                bbox: [-180.0, -90.0, 180.0, 90.0]
            }
        }
    },
    watch: {
        mode: function() {
            if (this.mode === 'editprediction') {
                this.prediction.modelId = this.model.modelId;
                this.prediction.version = '';
                this.prediction.tileZoom = 18;
                this.prediction.bbox = [-180.0, -90.0, 180.0, 90.0];
            }
        }
    },
    components: {
        EditPrediction
    },
    mounted: function() {
        this.getPredictions();
    },
    methods: {
        close: function() {
            this.$emit('close');
        },
        edit: function() {
            this.$emit('edit', this.model);
        },
        external: function(url) {
            if (!url) return;

            window.open(url, "_blank")
        },
        getPredictions: function() {
            fetch(`/v1/model/${this.model.modelId}/prediction/all`, {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((res) => {
                this.mode = 'model';

                if (res.error) {
                    this.predictions = [];
                } else {
                    this.predictions = res;
                }
            });
        }
    }
}
</script>
