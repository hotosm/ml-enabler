<template>
    <div class='col col--12'>
        <template v-if='loading'>
            <div class='flex-parent flex-parent--center-main w-full py24'>
                <div class='flex-child loading py24'></div>
            </div>
        </template>
        <template v-else-if='stack.status === "None"'>
            <h2 class='w-full align-center txt-h4 py12'>No Stack Deployed</h2>
            <div class='flex-parent flex-parent--center-main py12'>
                <button @click='createStack' class='flex-child btn btn--stroke round'>Create Stack</button>
            </div>
        </template>
        <template v-else-if='stack.status !== "None"'>
            <div class='flex-parent flex-parent--center-main w-full py24'>
                <div class='flex-child loading py24'></div>
            </div>
            <div class='flex-parent flex-parent--center-main w-full'>
                <div class='flex-child py24'><span v-text='stack.status'/></div>
            </div>
        </template>
    </div>
</template>

<script>

export default {
    name: 'Stack',
    props: ['model', 'prediction'],
    data: function() {
        return {
            loading: true,
            stack: {
                id: false,
                name: '',
                status: 'None'
            }
        };
    },
    mounted: function() {
        this.getStatus();
    },
    methods: {
        loop: function() {
            if (this.stack.status === 'None') return;

            setTimeout(() => {
                this.loop();
                this.getStatus();
            }, 5000);
        },
        getStatus: function() {
            this.loading = true;

            fetch(`${window.location.origin}/v1/model/${this.model.modelId}/prediction/${this.prediction.predictionsId}/stack`, {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((stack) => {
                this.stack = stack;
                this.loading = false;
            });
        },
        createStack: function() {
            this.loading = true;

            fetch(`${window.location.origin}/v1/model/${this.model.modelId}/prediction/${this.prediction.predictionsId}/stack`, {
                method: 'POST'
            }).then((res) => {
                return res.json();
            }).then((stack) => {
                this.stack = stack;
                this.loading = false;
                this.loop();
            });
        }
    }
}
</script>
