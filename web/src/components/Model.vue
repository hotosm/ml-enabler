<template>
    <div class="col col--12">
        <div class='col col--12 clearfix py6'>
            <h2 @click='mode = "model"' class='fl cursor-pointer txt-underline-on-hover' v-text='model.name + " - " + model.source'></h2>

            <button @click='close' class='btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-close'/></svg>
            </button>

            <button v-if='model.projectUrl' @click='external(model.projectUrl)' class='mr12 btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-link'/></svg>
            </button>

            <button v-if='mode === "model"' @click='edit' class='mr12 btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-pencil'/></svg>
            </button>

            <button @click='refresh' class='btn fr round btn--stroke color-gray color-blue-on-hover mr12'>
                <svg class='icon'><use href='#icon-refresh'/></svg>
            </button>
        </div>
        <div class='border border--gray-light round col col--12 px12 py12 clearfix'>
            <template v-if='mode === "model"'>
                <div class='col col--12 border-b border--gray-light clearfix'>
                    <h3 class='fl mt6 cursor-default'>Predictions:</h3>

                    <button @click='mode = "editPrediction"' class='btn fr mb6 round btn--stroke color-gray color-green-on-hover'>
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
                        <div :key='pred.predictionsId' v-for='pred in predictions' @click='showPrediction(pred)' class='cursor-pointer col col--12'>
                            <div class='col col--12 grid py6 px12 bg-darken10-on-hover'>
                                <div class='col col--6'>
                                    <div class='col col--12 clearfix'>
                                        <h3 class='txt-h4 fl' v-text='"v" + pred.versionString'></h3>
                                        <span class='fl ml6 bg-blue-faint bg-blue-on-hover color-white-on-hover color-blue inline-block px6 py3 round txt-xs txt-bold cursor-pointer' v-text='"id: " + pred.predictionsId'/>
                                    </div>
                                </div>
                                <div class='col col--6 clearfix'>
                                    <template v-if='!pred.modelLink'>
                                        <div class='fr bg-red-faint bg-red-on-hover color-white-on-hover color-red inline-block px6 py3 round txt-xs txt-bold cursor-pointer'>
                                            No Model
                                        </div>
                                    </template>

                                    <div v-if='pred.modelLink' class='fr mx3 bg-blue-faint bg-blue-on-hover color-white-on-hover color-blue inline-block px6 py3 round txt-xs txt-bold cursor-pointer'>
                                        Model
                                    </div>
                                    <div v-if='pred.saveLink' class='fr mx3 bg-blue-faint bg-blue-on-hover color-white-on-hover color-blue inline-block px6 py3 round txt-xs txt-bold cursor-pointer'>
                                        Container
                                    </div>
                                </div>
                            </div>
                        </div>

                    </template>
                </div>

                <div class='col col--12 border-b border--gray-light clearfix pt24'>
                    <h3 class='fl mt6 cursor-default'>Imagery:</h3>

                    <button @click='editImagery()' class='btn fr mb6 round btn--stroke color-gray color-green-on-hover'>
                        <svg class='icon'><use href='#icon-plus'/></svg>
                    </button>
                </div>

                <div class='grid grid--gut12'>
                    <template v-if='imagery.length === 0'>
                        <div class='col col--12 py6'>
                            <div class='flex-parent flex-parent--center-main pt36'>
                                <svg class='flex-child icon w60 h60 color--gray'><use href='#icon-info'/></svg>
                            </div>

                            <div class='flex-parent flex-parent--center-main pt12 pb36'>
                                <h1 class='flex-child txt-h4 cursor-default'>No Imagery Yet</h1>
                            </div>
                        </div>
                    </template>
                    <template v-else>
                        <div :key='img.id' v-for='img in imagery' @click='editImagery(img.id)' class='cursor-pointer col col--12'>
                            <div class='col col--12 grid py6 px12 bg-darken10-on-hover'>
                                <h3 class='txt-h4 fl' v-text='img.name'></h3>
                            </div>
                        </div>
                    </template>
                </div>
            </template>
            <template v-else-if='mode === "editImagery"'>
                <Imagery :modelid='model.modelId' :imageryid='imageryid' v-on:close='refresh'/>
            </template>
            <template v-else-if='mode === "editPrediction"'>
                <CreatePrediction :modelid='model.modelId' v-on:close='refresh' />
            </template>
            <template v-else-if='mode === "showPrediction"'>
                <Prediction :model='model' :prediction='prediction' v-on:close='refresh' />
            </template>
        </div>
    </div>
</template>

<script>
import vSort from 'semver-sort';
import Prediction from './Prediction.vue';
import CreatePrediction from './CreatePrediction.vue';
import Imagery from './Imagery.vue';

export default {
    name: 'Model',
    props: ['model'],
    data: function() {
        return {
            mode: 'model',
            predictions: [],
            imagery: [],
            imageryid: false,
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
            if (this.mode === 'editPrediction') {
                this.prediction.modelId = this.model.modelId;
                this.prediction.version = '';
                this.prediction.tileZoom = 18;
                this.prediction.bbox = [-180.0, -90.0, 180.0, 90.0];
            }
        }
    },
    components: {
        Imagery,
        Prediction,
        CreatePrediction
    },
    mounted: function() {
        this.refresh();
    },
    methods: {
        refresh: function() {
            this.mode = 'model';

            this.getPredictions();
            this.getImagery();
        },
        close: function() {
            this.$emit('close');
        },
        edit: function() {
            this.$emit('edit', this.model);
        },
        showPrediction: function(pred) {
            this.prediction = pred;
            this.mode = 'showPrediction';
        },
        external: function(url) {
            if (!url) return;

            window.open(url, "_blank")
        },
        editImagery: function(imgid) {
            if (imgid) {
                this.imageryid = imgid;
            } else {
                this.imageryid = false;
            }

            this.mode = 'editImagery';
        },
        getPredictions: function() {
            fetch(`/v1/model/${this.model.modelId}/prediction/all`, {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((res) => {
                if (res.error) {
                    this.predictions = [];
                } else {
                    const vMap = {};

                    for (const v of res) {
                        vMap[v.versionString] = v;
                    }

                    this.predictions = vSort.desc(res.map(r => r.versionString)).map(r => {
                        return vMap[r];
                    });
                }
            });
        },
        getImagery: function() {
            fetch(`/v1/model/${this.model.modelId}/imagery`, {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((res) => {
                if (res.error) {
                    this.imagery = [];
                } else {
                    this.imagery = res;
                }
            });
        }
    }
}
</script>
