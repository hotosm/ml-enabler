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

                    <div class='col col--12 py12'>
                        <button v-if='prediction.predictionsId' @click='postPrediction' class='btn btn--stroke round fr color-blue-light color-blue-on-hover'>Update Prediction</button>
                        <button v-else @click='postPrediction' class='btn btn--stroke round fr color-green-light color-green-on-hover'>Add Prediction</button>
                    </div>
                </template>
                <template v-else>
                    <div class='col col--12'>
                        <file-pond
                            name='model-upload'
                            ref='pond'
                            label-idle='Drop model.zip here'
                            v-bind:allow-multiple='false'
                            accepted-file-types='application/zip'
                            allowRevert='false'
                            :server='`/v1/model/${prediction.modelId}/prediction/${predictionId}/upload`'
                            v-bind:files='files'
                        />
                    </div>

                    <div class='col col--12 py12'>
                        <button @click='close' class='btn btn--stroke round fr color-blue-light color-blue-on-hover'>Done</button>
                    </div>
                </template>
            </div>
        </div>
    </div>

</template>

<script>
import vueFilePond from 'vue-filepond';
import 'filepond/dist/filepond.min.css';
import FilePondPluginFileValidateType from 'filepond-plugin-file-validate-type';
const FilePond = vueFilePond(FilePondPluginFileValidateType);

export default {
    name: 'EditPrediction',
    props: ['prediction'],
    components: {
        FilePond
    },
    data: function() {
        return {
            predictionId: false,
            upload: false,
            files: []
        };
    },
    watch: {
        predictionId: function() {
        }
    },
    methods: {
        close: function() {
            this.$emit('close');
        },
        postPrediction: function() {
            fetch(`/v1/model/${this.prediction.modelId}/prediction`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    modelId: this.prediction.modelId,
                    version: this.prediction.version,
                    tileZoom: this.prediction.tileZoom,
                    bbox: this.prediction.bbox
                })
            }).then((res) => {
                return res.json();
            }).then((res) => {
                this.predictionId = res.prediction_id;
            }).catch((err) => {
                alert(err);
            });
        }
    }
}
</script>
