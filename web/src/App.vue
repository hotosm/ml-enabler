<template>
    <div id="app" class='flex-parent flex-parent--center-main'>
        <div class='flex-child wmax600 col col--12'>
            <div class='flex-parent flex-parent--center-main py36'>
                <h1 @click='$router.push({ path: "/" })' class='flex-child txt-h3 cursor-default txt-underline-on-hover cursor-pointer'>ML Enabler</h1>
            </div>

            <router-view></router-view>
        </div>
    </div>
</template>

<script>
export default {
    name: 'MLEnabler',
    data: function() {
        return {
            stacks: {
                models: [],
                predictions: [],
                stacks: []
            },
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
    mounted: function() {
        this.refresh();
    },
    methods: {
        refresh: function() {
            this.getModels();
            this.getMeta();
            this.getStacks();
        },
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
            fetch(window.api + '/v1', {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((res) => {
                this.meta = res;
            }).catch((err) => {
                console.error(err);
            });
        },
        getStacks: function() {
            fetch(window.api + '/v1/stacks', {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((res) => {
                if (!res.error) {
                    this.stacks = res;
                }
            });
        },
        getModels: function() {
            this.mode = 'models';

            fetch(window.api + '/v1/model/all', {
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
            fetch(window.api + `/v1/model/${modelId}`, {
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
