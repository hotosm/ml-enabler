<template>
    <div class="col col--12">
        <div class='col col--12 clearfix py6'>
            <h2 class='fl cursor-default'>
                <span v-if='integrationid'>Update Integration</span>
                <span v-else=''>Add Integration</span>
            </h2>

            <button @click='close' class='btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-close'/></svg>
            </button>

            <button v-if='integrationid' @click='deleteIntegration' class='mr12 btn fr round btn--stroke color-gray color-red-on-hover'>
                <svg class='icon'><use href='#icon-trash'/></svg>
            </button>
        </div>
        <div class='border border--gray-light round col col--12 px12 py12 clearfix'>
            <div class='grid grid--gut12'>
                <div class='col col--12 py6'>
                    <label>Integration Name</label>
                    <input v-model='integration.name' class='input' placeholder='Integration Name'/>
                </div>

                <div class='col col--12 py6'>
                    <label>Integration Url</label>
                    <input v-model='integration.url' class='input' placeholder='Integration Name'/>
                </div>

                <div class='col col--12 py12'>
                    <template v-if='integrationid'>
                        <button @click='postIntegration' class='btn btn--stroke round fr color-blue-light color-green-on-hover'>Update Integration</button>
                    </template>
                    <template v-else>
                        <button @click='postIntegration' class='btn btn--stroke round fr color-green-light color-green-on-hover'>Add Integration</button>
                    </template>
                </div>
            </div>
        </div>
    </div>

</template>

<script>
export default {
    name: 'Integration',
    props: ['modelid', 'integrationid'],
    mounted: function() {
        this.integration.modelId = this.modelid;

        if (this.integrationid) {
            this.getIntegration();
        }
    },
    data: function() {
        return {
            integration: {
                integrationId: false,
                modelId: false,
                name: '',
                url: ''
            }
        };
    },
    methods: {
        close: function() {
            this.$emit('close');
        },
        getIntegration: async function() {
            try {
                const res = await fetch(window.api + `/v1/model/${this.modelid}/integration`, {
                    method: 'GET'
                });

                const body = await res.json();
                if (!res.ok) throw new Error(body.message);

                this.integrationid = body.filter((img) => {
                    return img.id === this.integrationId;
                })[0];
            } catch (err) {
                this.$emit('err', err);
            }
        },
        deleteIntegration: async function() {
            try {
                const res = await fetch(window.api + `/v1/model/${this.modelid}/imagery/${this.imageryid}`, {
                    method: 'DELETE'
                });
                const body = await res.json();
                if (!res.ok) throw new Error(body.message);
                this.close();
            } catch (err) {
                this.$emit('err', err);
            }
        },
        postIntegration: async function() {
            try {
                const res = await fetch(window.api + `/v1/model/${this.modelid}/imagery${this.imageryid ? '/' + this.imageryid : ''}`, {
                    method: this.imageryid ? 'PATCH' : 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        modelId: this.imagery.modelId,
                        name: this.imagery.name,
                        url: this.imagery.url
                    })
                });

                const body = await res.json();
                if (!res.ok) throw new Error(body.message);
                this.imagery.imageryId = body.imageryId;
                this.close();
            } catch (err) {
                this.$emit('err', err);
            }
        }
    }
}
</script>
