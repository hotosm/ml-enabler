<template>
    <div class="col col--12">
        <div class='col col--12 clearfix py6'>
            <h2 class='fl cursor-default' v-text='model.name + " - " + model.source'></h2>

            <button @click='close' class='btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-close'/></svg>
            </button>

            <button @click='external(model.projectUrl)' class='mr12 btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-link'/></svg>
            </button>

            <button @click='edit' class='mr12 btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-pencil'/></svg>
            </button>
        </div>
        <div class='border border--gray-light round col col--12 px12 py12 clearfix'>
            <div class='col col--12 border-b border--gray-light clearfix'>
                <h3 class='fl mt6 cursor-default'>Predictions:</h3>

                <button class='btn fr mb6 round btn--stroke color-gray color-green-on-hover'>
                    <svg class='icon'><use href='#icon-plus'/></svg>
                </button>
            </div>

            <div class='grid grid--gut12'>
                <template v-if='predictions.length === 0'>
                    <div class='col col--12 py6'>
                        <div class='flex-parent flex-parent--center-main pt36'>
                            <svg class='flex-child icon w60 h60 color--gray'><use href='#icon-info'/></svg>
                        </div>

                        <div class='flex-parent flex-parent--center-main pt12 pb36'>
                            <h1 class='flex-child txt-h4 cursor-default'>No Predictions Yet</h1>
                        </div>
                    </div>
                </template>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'Model',
    props: ['model'],
    data: function() {
        return {
            predictions: []
        }
    },
    mounted: function() {
        this.getPredictions();
    },
    methods: {
        close: function() {
            this.$emit('close');
        },
        edit: function() {
            this.$emit('edit', this.model);
        },
        external: function(url) {
            if (!url) return;

            window.open(url, "_blank")
        },
        getPredictions: function() {
            fetch(`/v1/model/${this.model.modelId}/prediction/all`, {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((res) => {
                if (res.error) {
                    this.predictions = [];
                } else {
                    this.predictions = res;
                }
            });
        }
    }
}
</script>
