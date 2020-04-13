<template>
    <div id="app" class='flex-parent flex-parent--center-main'>
        <div class='flex-child wmax600 col col--12'>
            <div class='flex-parent flex-parent--center-main py36'>
                <h1 @click='mode = "models"' class='flex-child txt-h3 cursor-default txt-underline-on-hover cursor-pointer'>ML Enabler</h1>
            </div>

            <template v-if='mode === "models"'>
                <div class='col col--12 clearfix py6'>
                    <h2 class='fl cursor-default'>Models</h2>

                    <button @click='$router.push({ name: "editmodel' })' class='btn fr round btn--stroke color-gray color-green-on-hover'>
                        <svg class='icon'><use href='#icon-plus'/></svg>
                    </button>
                    <button @click='getModels' class='btn fr round btn--stroke color-gray color-blue-on-hover mr12'>
                        <svg class='icon'><use href='#icon-refresh'/></svg>
                    </button>
                </div>
                <div class='border border--gray-light round'>
                    <template v-if='models.length === 0'>
                        <div class='flex-parent flex-parent--center-main pt36'>
                            <svg class='flex-child icon w60 h60 color--gray'><use href='#icon-info'/></svg>
                        </div>

                        <div class='flex-parent flex-parent--center-main pt12 pb36'>
                            <h1 class='flex-child txt-h4 cursor-default'>Create a model to get started!</h1>
                        </div>
                    </template>
                    <template v-else>
                        <div @click='showModel(model)' :key='model.modelId' v-for='model in models' class='cursor-pointer bg-darken10-on-hover col col--12 py12'>
                            <div class='col col--12 grid py6 px12'>
                                <div class='col col--6'>
                                    <div class='col col--12 clearfix'>
                                        <h3 class='txt-h4 fl' v-text='model.name'></h3>
                                        <svg @click.prevent.stop='editModel(model.modelId)' class='fl my6 mx6 icon cursor-pointer color-gray-light color-gray-on-hover'><use href='#icon-pencil'/></svg>
                                    </div>
                                    <div class='col col--12'>
                                        <h3 class='txt-xs' v-text='model.source'></h3>
                                    </div>
                                </div>
                                <div class='col col--6'>
                                    <div @click.prevent.stop='external(model.projectUrl)' class='fr bg-blue-faint bg-blue-on-hover color-white-on-hover color-blue inline-block px6 py3 round txt-xs txt-bold cursor-pointer'>
                                        Project Page
                                    </div>
                                </div>
                            </div>
                        </div>
                    </template>
                </div>
            </template>
            <template v-else>
                <router-view></router-view>
            <template v-else-if='mode === "editmodel"'>
                <EditModel :model='JSON.parse(JSON.stringify(model))' v-on:close='getModels'/>
            </template>
            <template v-else-if='mode === "model"'>
                <Model
                    :model='JSON.parse(JSON.stringify(model))'
                    :meta='meta'
                    v-on:close='getModels'
                    v-on:edit='editModel($event.modelId)'
                />
            </template>

        </div>
    </div>
</template>

<script>
            /*<template v-else-if='mode === "editmodel"'>
                <EditModel :model='JSON.parse(JSON.stringify(model))' v-on:close='getModels'/>
            </template>
            <template v-else-if='mode === "model"'>
                <Model :model='JSON.parse(JSON.stringify(model))' v-on:close='getModels' v-on:edit='editModel($event.modelId)'/>
            </template>*/

export default {
    name: 'MLEnabler',
    data: function() {
        return {
            mode: 'models',
            model: {
                modelId: false,
                name: '',
                source: '',
                projectUrl: ''
            },
            meta: {
                version: 1,
                environemnt: 'docker'
            },
            models: []
        }
    },
    watch: {
        mode: function() {
            if (this.mode === 'editmodel') {
                this.model.modelId = false;
                this.model.name = '';
                this.model.source = '';
                this.model.projectUrl = '';
            }
        }
    },
    mounted: function() {
        this.getModels();
    },
    methods: {
        external: function(url) {
            if (!url) return;

            window.open(url, "_blank")
        },
        showModel: function(model) {
            this.model.modelId = model.modelId;
            this.model.name = model.name;
            this.model.source = model.source;
            this.model.projectUrl = model.projectUrl;
            this.mode = 'model'
        },
        editModel: function(modelId) {
            if (!modelId) return;

            this.mode = 'editmodel';
            this.getModel(modelId);
        },
        getMeta: function() {
            fetch('/v1', {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((res) => {
                this.meta = res;
            }).catch((err) => {
                console.error(err);
            });
        },
        getModels: function() {
            this.mode = 'models';

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
        getModel: function(modelId) {
            fetch(`/v1/model/${modelId}`, {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((res) => {
                this.model = res;
            });
        }
    }
}
</script>
