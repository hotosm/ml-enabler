<template>
    <div class="col col--12">
        <div class='col col--12 clearfix py6'>
            <h2 v-if='!newModel' class='fl'>Modify Model</h2>
            <h2 v-else class='fl cursor-default'>Add Model</h2>

            <button @click='$router.push({ path: "/" });' class='btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-close'/></svg>
            </button>

            <button v-if='!newModel' @click='deleteModel($route.params.modelid)' class='mr12 btn fr round btn--stroke color-gray color-red-on-hover'>
                <svg class='icon'><use href='#icon-trash'/></svg>
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
                    <label>Project Url</label>
                    <input v-model='model.projectUrl' class='input' placeholder='Docker Hub'/>
                </div>

                <div class='col col--12 py12'>
                    <button v-if='!newModel' @click='postModel(true)' class='btn btn--stroke round fl color-gray color-red-on-hover'>Archive Model</button>
                    <button v-if='!newModel' @click='postModel' class='btn btn--stroke round fr color-blue-light color-blue-on-hover'>Update Model</button>
                    <button v-else @click='postModel' class='btn btn--stroke round fr color-green-light color-green-on-hover'>Add Model</button>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'EditModel',
    props: ['meta'],
    data: function() {
        return {
            newModel: this.$route.name === 'newmodel',
            model: {}
        }
    },
    mounted: function() {
        this.getModel();
    },
    methods: {
        postModel: function(archive) {
            fetch(window.api + `/v1/model${!this.newModel ? '/' + this.$route.params.modelid : ''}`, {
                method: this.$route.params.modelid ? 'PUT' : 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    modelId: !this.newModel ? this.$route.params.modelid : undefined,
                    name: this.model.name,
                    source: this.model.source,
                    projectUrl: this.model.projectUrl,
                    archived: archive ? true : false
                })
            }).then(() => {
                this.$router.push({ path: '/' });
            });
        },
        getModel: function() {
            if (this.$route.name === "newmodel") return;

            fetch(window.api + `/v1/model/${this.$route.params.modelid}`, {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((res) => {
                this.model = res;
            });
        },
        deleteModel: function() {
            fetch(window.api + `/v1/model/${this.$route.params.modelid}`, {
                method: 'DELETE'
            }).then((res) => {
                return res.json();
            }).then(() => {
                this.$router.push({ path: '/' });
            });
        }
    }
}
</script>
