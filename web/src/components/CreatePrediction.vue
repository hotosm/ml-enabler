<template>
    <div class="col col--12">
        <div class='col col--12 clearfix py6'>
            <h2 class='fl cursor-default'>Add Prediction</h2>

            <button @click='close' class='btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-close'/></svg>
            </button>
        </div>
        <div class='border border--gray-light round col col--12 px12 py12 clearfix'>
            <div class='grid grid--gut12'>
                <template v-if='!predictionId'>
                    <div class='col col--6 py6'>
                        <label>Prediction Version</label>
                        <input v-model='prediction.version' class='input' placeholder='0.0.0'/>
                    </div>

                    <div class='col col--6 py6'>
                        <label>Prediction Zoom Level</label>
                        <input v-model='prediction.tileZoom' class='input' placeholder='18'/>
                    </div>
                    <div class='col col--4'>
                        <label>Model Type:</label>
                        <div class='select-container'>
                            <select v-model='prediction.infType' class='select'>
                                <option value='classification'>Classification</option>
                                <option value='detection'>Object Detection</option>
                            </select>
                            <div class='select-arrow'></div>
                        </div>
                    </div>

                    <template v-if='prediction.infType === "classification"'>
                        <div class='col col--8'>
                            <label>Inferences List:</label>
                            <label class='switch-container px6 fr'>
                                <span class='mr6'>Binary Inference</span>
                                <input :disabled='prediction.infList.split(",").length !== 2' v-model='prediction.infBinary' type='checkbox' />
                                <div class='switch'></div>
                            </label>
                            <input v-model='prediction.infList' type='text' class='input' placeholder='buildings,schools,roads,...'/>
                        </div>
                        <div class='col col--8'>
                        </div>
                    </template>
                    <div class='col col--4'>
                        <label class='switch-container px6 fr'>
                            <span class='mr6'>Supertile</span>
                            <input :disabled='prediction.infType == "detection"' v-model='prediction.infSupertile' type='checkbox' />
                            <div class='switch'></div>
                        </label>
                    </div>
                    <div class='col col--8'></div>
                    <div class='col col--12 py12'>
                        <button @click='postPrediction' class='btn btn--stroke round fr color-green-light color-green-on-hover'>Add Prediction</button>
                    </div>
                </template>
            </div>
        </div>
    </div>

</template>

<script>
export default {
    name: 'CreatePrediction',
    props: ['modelid'],
    mounted: function() {
        this.prediction.modelId = this.modelid;
    },
    data: function() {
        return {
            predictionId: false,
            prediction: {
                modelId: false,
                predictionsId: false,
                version: '',
                tileZoom: '18',
                infList: '',
                infType: 'classification',
                infBinary: false,
                infSupertile: false
            }
        };
    },
    watch: {
        'prediction.infList': function() {
            if (this.prediction.infList.split(",").length !== 2) {
                this.prediction.infBinary = false;
            }
        }
    },
    methods: {
        close: function() {
            this.$emit('close');
        },
        postPrediction: async function() {
            if (!/^\d+\.\d+\.\d+$/.test(this.prediction.version)) {
                return this.$emit('err', new Error('Version must be valid semver'));
            } else if (this.prediction.infType === 'classification' && this.prediction.infList.trim().length === 0) {
                return this.$emit('err', new Error('Classification model must have inference list'));
            } else if (isNaN(parseInt(this.prediction.tileZoom))) {
                return this.$emit('err', new Error('Tile Zoom must be an integer'));
            }

            try {
                let res = await fetch(window.api + `/v1/model/${this.modelid}/prediction`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        modelId: this.prediction.modelId,
                        version: this.prediction.version,
                        tileZoom: this.prediction.tileZoom,
                        bbox: [-180.0, -90.0, 180.0, 90.0],
                        infList: this.prediction.infList,
                        infType: this.prediction.infType,
                        infBinary: this.prediction.infBinary,
                        infSupertile: this.prediction.infSupertile
                    })
                });

                if (!res.ok) {
                    res = await res.json();
                    if (res.message) {
                        return this.$emit('err', new Error(res.message));
                    } else {
                        return this.$emit('err', new Error('Failed to post prediction'));
                    }
                }

                res = await res.json();
                this.predictionId = res.prediction_id;
                this.prediction.predictionsId = res.prediction_id;
                this.close();
            } catch(err) {
                return this.$emit('err', err);
            }
        }
    }
}
</script>
