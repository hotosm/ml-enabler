<template>
    <div class="col col--12">
        <div class='col col--12 clearfix py6'>
            <h2 class='fl cursor-default'>Add Imagery</h2>

            <button @click='close' class='btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-close'/></svg>
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
                    <button @click='postImagery' class='btn btn--stroke round fr color-green-light color-green-on-hover'>Add Imagery</button>
                </div>
            </div>
        </div>
    </div>

</template>

<script>
export default {
    name: 'Imagery',
    props: ['modelid'],
    mounted: function() {
        this.imagery.modelId = this.modelid;
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
        postImagery: function() {
            fetch(`/v1/model/${this.modelid}/imagery`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    modelId: this.imagery.modelId,
                    name: this.imagery.name,
                    url: this.imagery.url
                })
            }).then((res) => {
                return res.json();
            }).then((res) => {
                this.imagery.imageryId = res.imageryId;
            }).catch((err) => {
                alert(err);
            });
        }
    }
}
</script>
