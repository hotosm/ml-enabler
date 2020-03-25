<template>
    <div class='col col--12 relative'>
        <div class='absolute right top'>
            <button @click='refresh' class='btn fr round btn--stroke btn--gray'>
                <svg class='icon'><use href='#icon-refresh'/></svg>
            </button>

            <button v-if='stack.status === "CREATE_COMPLETE"' @click='deleteStack' class='mr12 btn fr round btn--stroke color-gray color-red-on-hover'>
                <svg class='icon'><use href='#icon-trash'/></svg>
            </button>
        </div>

        <template v-if='loading'>
            <div class='flex-parent flex-parent--center-main w-full py24'>
                <div class='flex-child loading py24'></div>
            </div>
        </template>
        <template v-else-if='stack.status === "None"'>
            <h2 class='w-full align-center txt-h4 py12'>No Stack Deployed</h2>
            <div class='flex-parent flex-parent--center-main py12'>
                <button @click='createStack' class='flex-child btn btn--stroke color-gray color-green-on-hover round'>Create Stack</button>
            </div>
        </template>
        <template v-else-if='stack.status === "CREATE_COMPLETE"'>
            <div class='col col--12 grid'>
                <div class='col col--12 grid'>
                    <span v-text='stack.name'/>
                </div>
                <div class='col col--12 pt12 flex-parent flex-parent--center-main'>
                    Imagery Chip Submission
                </div>
                <div class='col col--6'>
                    <div class='flex-parent flex-parent--center-main py12'>
                        <button @click='createStack' style='width: 200px;' class='flex-child btn btn--stroke round btn--gray'>ZXY List</button>
                    </div>
                </div>
                <div class='col col--6'>
                    <div class='flex-parent flex-parent--center-main py12'>
                        <button @click='createStack' style='width: 200px;' class='flex-child btn btn--stroke round btn--gray'>Bounding Box</button>
                    </div>
                </div>
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
            looping: false,
            stack: {
                id: false,
                name: '',
                status: 'None'
            }
        };
    },
    mounted: function() {
        this.refresh();
    },
    methods: {
        refresh: function() {
            this.getStatus();
        },
        loop: function() {
            this.looping = true;

            if ([
                'None',
                'CREATE_COMPLETE',
                'DELETE_COMPLETE'
            ].includes(this.stack.status)) {
                this.looping = false;
                return;
            }

            setTimeout(() => {
                if ([
                    'None',
                    'CREATE_COMPLETE',
                    'DELETE_COMPLETE'
                ].includes(this.stack.status)) {
                    this.looping = false;
                    return;
                }

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

                if (!this.looping) this.loop();
            });
        },
        deleteStack: function() {
            this.loading = true;

            fetch(`${window.location.origin}/v1/model/${this.model.modelId}/prediction/${this.prediction.predictionsId}/stack`, {
                method: 'DELETE'
            }).then((res) => {
                return res.json();
            }).then((stack) => {
                this.stack = stack;
                this.loading = false;

                if (!this.looping) this.loop();
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

                if (!this.looping) this.loop();
            });
        }
    }
}
</script>
