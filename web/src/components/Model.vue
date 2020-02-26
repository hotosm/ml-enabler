<template>
    <div class="col col--12">
        <div class='col col--12 clearfix py6'>
            <h2 class='fl cursor-default' v-text='model.name + " - " + model.source'></h2>

            <button @click='mode = "models"' class='btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-close'/></svg>
            </button>

            <button @click='external(model.projectUrl)' class='mr12 btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-link'/></svg>
            </button>

            <button @click='editModel(model.modelId)' class='mr12 btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-pencil'/></svg>
            </button>
        </div>
        <div class='border border--gray-light round col col--12 px12 py12 clearfix'>
            <div class='grid grid--gut12'>
                <div class='col col--12 py6'>
                    <template v-if='models.length === 0'>
                        <div class='flex-parent flex-parent--center-main pt36'>
                            <svg class='flex-child icon w60 h60 color--gray'><use href='#icon-info'/></svg>
                        </div>

                        <div class='flex-parent flex-parent--center-main pt12 pb36'>
                            <h1 class='flex-child txt-h4 cursor-default'>Create a model to get started!</h1>
                        </div>
                    </template>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'Model',
    props: ['model'],
    methods: {
        close: function() {
            this.$emit('close');
        },
    }
}
</script>
