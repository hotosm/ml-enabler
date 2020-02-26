<template>
    <div class="col col--12">
        <div class='col col--12 clearfix py6'>
            <h2 v-if='model.modelId' class='fl'>Modify Model</h2>
            <h2 v-else class='fl cursor-default'>Add Model</h2>

            <button @click='close' class='btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-close'/></svg>
            </button>

            <button v-if='model.modelId' @click='deleteModel(model.modelId)' class='mr12 btn fr round btn--stroke color-gray color-red-on-hover'>
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
                    <button v-if='model.modelId' @click='postModel' class='btn btn--stroke round fr color-blue-light color-blue-on-hover'>Update Model</button>
                    <button v-else @click='postModel' class='btn btn--stroke round fr color-green-light color-green-on-hover'>Add Model</button>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'EditModel',
    props: ['model'],
    methods: {
        close: function() {
            this.$emit('close');
        },
        postModel: function() {
            fetch(`/v1/model${this.model.modelId ? '/' + this.model.modelId : ''}`, {
                method: this.model.modelId ? 'PUT' : 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    modelId: this.model.modelId ? this.model.modelId : undefined,
                    name: this.model.name,
                    source: this.model.source,
                    projectUrl: this.model.projectUrl
                })
            }).then(() => {
                this.close();
            });
        },
        deleteModel: function() {
            fetch(`/v1/model/${modelId}`, {
                method: 'DELETE'
            }).then((res) => {
                return res.json();
            }).then(() => {
                this.close();
            });
        }
    }
}
</script>
