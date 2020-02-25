<template>
    <div id="app" class='flex-parent flex-parent--center-main'>
        <div class='flex-child wmax600 col col--12'>
            <div class='flex-parent flex-parent--center-main py36'>
                <h1 class='flex-child txt-h3'>ML Enabler</h1>
            </div>

            <h2>Models</h2>
            <div class='border round'>
                <template v-for='model in models'>
                    <div class='col col--12 py12'>
                        <div class='col col--12'>
                            <h3 v-text='model.name'></h3>
                        </div>
                    </div>
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
                this.models = res;
            });
        }
    }
}
</script>
