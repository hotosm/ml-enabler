<template>
    <div id="app" class='flex-parent flex-parent--center-main'>
        <div class='flex-child wmax600 col col--12'>
            <div class='flex-parent flex-parent--center-main py36'>
                <h1 class='flex-child txt-h3'>ML Enabler</h1>
            </div>

            <div class='col col--12 clearfix py6'>
                <h2 class='fl'>Models</h2>

                <button class='btn fr round btn--stroke color-gray color-green-on-hover'>
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
                    <template v-for='model in models'>
                        <div class='col col--12 py12'>
                            <div class='col col--12'>
                                <h3 v-text='model.name'></h3>
                            </div>
                        </div>
                    </template>
                </template>
            </div>
        </div>
    </div>
</template>

<script>

export default {
    name: 'MLEnabler',
    data: function() {
        return {
            models: []
        }
    },
    mounted: function() {
        this.fetchModels();
    },
    methods: {
        fetchModels: function() {
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
        }
    }
}
</script>
