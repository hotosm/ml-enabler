<template>
    <div class="col col--12">
        <div class='col col--12 clearfix py6'>
            <h2 class='fl cursor-default'>
                <span v-if='imageryid'>Update Imagery</span>
                <span v-else=''>Add Imagery</span>
            </h2>

            <button @click='close' class='btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-close'/></svg>
            </button>

            <button v-if='imageryid' @click='deleteImagery' class='mr12 btn fr round btn--stroke color-gray color-red-on-hover'>
                <svg class='icon'><use href='#icon-trash'/></svg>
            </button>
        </div>
        <div class='border border--gray-light round col col--12 px12 py12 clearfix'>
            <div class='grid grid--gut12'>
                <div class='col col--12 py6'>
                    <label>Imagery Name</label>
                    <input v-model='imagery.name' class='input' placeholder='Imagery Name'/>
                </div>

                <div class='col col--12 py6'>
                    <label>Imagery Url</label>
                    <input v-model='imagery.url' class='input' placeholder='Imagery Name'/>
                </div>

                <div class='col col--12 py12'>
                    <template v-if='imageryid'>
                        <button @click='postImagery' class='btn btn--stroke round fr color-blue-light color-green-on-hover'>Update Imagery</button>
                    </template>
                    <template v-else>
                        <button @click='postImagery' class='btn btn--stroke round fr color-green-light color-green-on-hover'>Add Imagery</button>
                    </template>
                </div>
            </div>
        </div>
    </div>

</template>

<script>
export default {
    name: 'Imagery',
    props: ['modelid', 'imageryid'],
    mounted: function() {
        this.imagery.modelId = this.modelid;

        if (this.imageryid) {
            this.getImagery();
        }
    },
    data: function() {
        return {
            imagery: {
                imageryId: false,
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
        getImagery: async function() {
            try {
                const res = await fetch(window.api + `/v1/model/${this.modelid}/imagery`, {
                    method: 'GET'
                });

                const body = await res.json();
                if (!res.ok) throw new Error(body.message);

                this.imagery = body.filter((img) => {
                    return img.id === this.imageryid;
                })[0];
            } catch (err) {
                this.$emit('err', err);
            }
        },
        deleteImagery: async function() {
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
        postImagery: async function() {
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
