<template>
    <div id="app" class='flex-parent flex-parent--center-main'>
        <div class='flex-child wmax600 col col--12'>
            <div class='flex-parent flex-parent--center-main py36'>
                <h1 class='flex-child txt-h3'>ML Enabler</h1>
            </div>

            <template v-if='mode === "models"'>
                <div class='col col--12 clearfix py6'>
                    <h2 class='fl'>Models</h2>

                    <button @click='mode = "create"' class='btn fr round btn--stroke color-gray color-green-on-hover'>
                        <svg class='icon'><use href='#icon-plus'/></svg>
                    </button>
                </div>
                <div class='border border--gray-light round'>
                    <template v-if='models.length === 0'>
                        <div class='flex-parent flex-parent--center-main pt36'>
                            <svg class='flex-child icon w60 h60 color--gray'><use href='#icon-info'/></svg>
                        </div>

                        <div class='flex-parent flex-parent--center-main pt12 pb36'>
                            <h1 class='flex-child txt-h4'>Create a model to get started!</h1>
                        </div>
                    </template>
                    <template v-else>
                        <div v-for='model in models' class='col col--12 py12'>
                            <div class='col col--12'>
                                <h3 v-text='model.name'></h3>
                            </div>
                        </div>
                    </template>
                </div>
            </template>
            <template v-else-if='mode === "create"'>
                <div class='col col--12 clearfix py6'>
                    <h2 class='fl'>Add Model</h2>

                    <button @click='mode = "models"' class='btn fr round btn--stroke color-gray color-black-on-hover'>
                        <svg class='icon'><use href='#icon-close'/></svg>
                    </button>
                </div>
                <div class='border border--gray-light round col col--12 px12 py12 clearfix'>
                    <div class='grid grid--gut12'>
                        <div class='col col--12 py6'>
                            <label>Model Name</label>
                            <input v-model='model.name' class='input' placeholder='Model Name'/>
                        </div>

                        <div class='col col--6 py6'>
                            <label>Model Source</label>
                            <input v-model='model.source' class='input' placeholder='Company'/>
                        </div>

                        <div class='col col--6 py6'>
                            <label>Model Location</label>
                            <input v-model='model.dockerhubUrl' class='input' placeholder='Docker Hub'/>
                        </div>

                        <div class='col col--12 py12'>
                            <button @click='postModel' class='btn btn--stroke round fr color-green-light color-green-on-hover'>Add Model</button>
                        </div>
                    </div>
                </div>
            </template>
        </div>
    </div>
</template>

<script>

export default {
    name: 'MLEnabler',
    data: function() {
        return {
            mode: 'models',
            model: {
                name: '',
                source: '',
                dockerhubUrl: ''
            },
            models: []
        }
    },
    watch: {
        mode: function() {
            if (this.mode === 'create') {
                this.model.name = '';
                this.model.source = '';
                this.model.dockerhubUrl = '';
            }
        }
    },
    mounted: function() {
        this.getModels();
    },
    methods: {
        getModels: function() {
            fetch('/v1/model/all', {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((res) => {
                if (res.error && res.error === 'no models found') {
                    this.models = [];
                } else {
                    this.models = res;
                }
            });
        },
        postModel: function() {
            fetch('/v1/model', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: this.model.name,
                    source: this.model.source,
                    dockerhubUrl: this.model.dockerhubUrl
                })
            }).then(() => {
                this.getModels();
                this.mode = "models";
            });
        }
    }
}
</script>
