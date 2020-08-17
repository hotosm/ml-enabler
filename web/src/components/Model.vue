<template>
    <div class="col col--12">
        <template v-if='loading.model'>
            <div class='flex-parent flex-parent--center-main w-full py24'>
                <div class='flex-child loading py24'></div>
            </div>
        </template>
        <template v-else-if='$route.name === "model"'>
            <div class='col col--12 clearfix py6'>
                <h2 @click='$router.push({ name: "home" })' class='fl cursor-pointer txt-underline-on-hover'>Models</h2>
                <h2 class='fl px6'>&gt;</h2>
                <h2 @click='mode = "model"' class='fl cursor-pointer txt-underline-on-hover' v-text='model.name + " - " + model.source'></h2>

                <button @click='$router.push({ name: "home" })' class='btn fr round btn--stroke color-gray color-black-on-hover'>
                    <svg class='icon'><use href='#icon-close'/></svg>
                </button>

                <button v-if='model.projectUrl' @click='external(model.projectUrl)' class='mr12 btn fr round btn--stroke color-gray color-black-on-hover'>
                    <svg class='icon'><use href='#icon-link'/></svg>
                </button>

                <button v-if='mode === "model"' @click='$router.push({ name: "editmodel", params: { modelid: $route.params.modelid } })' class='mr12 btn fr round btn--stroke color-gray color-black-on-hover'>
                    <svg class='icon'><use href='#icon-pencil'/></svg>
                </button>

                <button v-if='mode === "model"' @click='refresh' class='btn fr round btn--stroke color-gray color-blue-on-hover mr12'>
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
                            <div :key='pred.predictionsId' v-for='pred in predictions' @click='$router.push({ name: "prediction", params: {
                                modelid: $route.params.modelid,
                                predid: pred.predictionsId
                            }})' class='cursor-pointer col col--12'>
                                <div class='col col--12 grid py6 px12 bg-darken10-on-hover'>
                                    <div class='col col--6'>
                                        <div class='col col--12 clearfix'>
                                            <h3 class='txt-h4 fl' v-text='"v" + pred.version'></h3>
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
                                        <div v-if='stacks.predictions.includes(pred.predictionsId)' class='fr bg-green-faint bg-green-on-hover color-white-on-hover color-green inline-block px6 py3 round txt-xs txt-bold mr3'>
                                            Active Stack
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
                    <div class='col col--12 border-b border--gray-light clearfix pt24'>
                        <h3 class='fl mt6 cursor-default'>Integrations:</h3>

                        <button @click='editIntegration()' class='btn fr mb6 round btn--stroke color-gray color-green-on-hover'>
                            <svg class='icon'><use href='#icon-plus'/></svg>
                        </button>
                    </div>

                    <Integrations @integration='editIntegration($event.id)'/>
                </template>
                <template v-else-if='mode === "editIntegration"'>
                    <Integration @err='$emit("err", $event)' :modelid='model.modelId' :integrationid='integrationid' @close='refresh'/>
                </template>
                <template v-else-if='mode === "editImagery"'>
                    <Imagery @err='$emit("err", $event)' :modelid='model.modelId' :imageryid='imageryid' @close='refresh'/>
                </template>
                <template v-else-if='mode === "editPrediction"'>
                    <CreatePrediction @err='$emit("err", $event)' :modelid='model.modelId' @close='refresh' />
                </template>
            </div>
        </template>
        <template v-else>
            <router-view
                :meta='meta'
                :model='model'
                @refresh='refresh'
                @err='$emit("err", $event)'
            />
        </template>
    </div>
</template>

<script>
import vSort from 'semver-sort';
import Imagery from './Imagery.vue';
import Integration from './Integration.vue';
import Integrations from './Integrations.vue';
import CreatePrediction from './CreatePrediction.vue';

export default {
    name: 'Model',
    props: ['meta', 'stacks'],
    data: function() {
        return {
            mode: 'model',
            predictions: [],
            model: {},
            imagery: [],
            integrations: [],
            imageryid: false,
            integrationid: false,
            loading: {
                model: true
            },
            prediction: {
                modelId: this.$route.params.modelid,
                version: '',
                tileZoom: 18,
                bbox: [-180.0, -90.0, 180.0, 90.0]
            }
        }
    },
    watch: {
        mode: function() {
            if (this.mode === 'editPrediction') {
                this.prediction.modelId = this.$route.params.modelid;
                this.prediction.version = '';
                this.prediction.tileZoom = 18;
                this.prediction.bbox = [-180.0, -90.0, 180.0, 90.0];
            }
        }
    },
    components: {
        Imagery,
        Integration,
        Integrations,
        CreatePrediction
    },
    mounted: function() {
        this.refresh();
    },
    methods: {
        refresh: function() {
            this.mode = 'model';

            this.getPredictions();
            this.getModel();
            this.getImagery();
            this.getIntegration();
        },
        close: function() {
            this.$emit('close');
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
        editIntegration: function(intid) {
            if (intid) {
                this.integrationid = intid;
            } else {
                this.integrationid = false;
            }

            this.mode = 'editIntegration';
        },
        getPredictions: async function() {
            try {
                const res = await fetch(window.api + `/v1/model/${this.$route.params.modelid}/prediction/all`, {
                    method: 'GET'
                });

                const body = await res.json();
                if (!res.ok) throw new Error(body.message);
                const vMap = {};

                for (const v of body) {
                    vMap[v.version] = v;
                }

                this.predictions = vSort.desc(body.map(r => r.version)).map(r => {
                    return vMap[r];
                });
            } catch (err) {
                this.$emit('err', err);
            }
        },
        getModel: async function() {
            this.loading.model = true;

            try {
                const res = await fetch(window.api + `/v1/model/${this.$route.params.modelid}`, {
                    method: 'GET'
                });

                const body = await res.json();

                this.loading.model = false;
                if (!res.ok) throw new Error(body.message);
                this.model = body;
            } catch (err) {
                this.$emit('err', err);
            }
        },
        getImagery: async function() {
            try {
                const res = await fetch(window.api + `/v1/model/${this.$route.params.modelid}/imagery`, {
                    method: 'GET'
                });

                const body = await res.json();
                if (!res.ok) throw new Error(body.message);
                this.imagery = body;
            } catch (err) {
                this.$emit('err', err);
            }
        },
        getIntegration: async function() {
            try {
                const res = await fetch(window.api + `/v1/model/${this.$route.params.modelid}/integration`, {
                    method: 'GET'
                });

                const body = await res.json();
                if (!res.ok) throw new Error(body.message);
                this.integrations = body;
            } catch (err) {
                this.$emit('err', err);
            }
        }
    }
}
</script>
