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
                            <input v-model='prediction.infList' type='text' class='input' placeholder='buildings,schools,roads,...'/>
                        </div>
                    </template>
                    <template v-if='prediction.infList.split(",").length === 2'>
                        <div class='col col--4'>
                            <label class='checkbox-container px6'>
                                Binary Inference:
                                <input v-model='prediction.infBinary' type='checkbox' />
                                <div class='checkbox mx6'>
                                    <svg class='icon'><use xlink:href='#icon-check' /></svg>
                                </div>
                            </label>
                        </div>
                        <div class='col col--8'>
                        </div>

                    </template>
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
                bbox: [-180.0, -90.0, 180.0, 90.0],
                infList: '',
                infType: 'classification',
                infBinary: false
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
        postPrediction: function() {
            fetch(window.api + `/v1/model/${this.modelid}/prediction`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    modelId: this.prediction.modelId,
                    version: this.prediction.version,
                    tileZoom: this.prediction.tileZoom,
                    bbox: this.prediction.bbox,
                    infList: this.prediction.infList,
                    infType: this.prediction.infType,
                    infBinary: this.prediction.infBinary
                })
            }).then((res) => {
                return res.json();
            }).then((res) => {
                this.predictionId = res.prediction_id;
                this.prediction.predictionsId = res.prediction_id;
                this.close();
            }).catch((err) => {
                alert(err);
            });
        }
    }
}
</script>
