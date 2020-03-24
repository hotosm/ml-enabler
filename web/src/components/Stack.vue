<template>
    <div class='col col--12'>
        <template v-if='!stack'>
            <h2 class='w-full align-center txt-h4 py12'>No Stack Deployed</h2>
            <div class='flex-parent flex-parent--center-main py12'>
                <button class='flex-child btn btn--stroke round'>Create Stack</button>
            </div>
        </template>
    </div>
</template>

<script>

export default {
    name: 'Stack',
    props: ['prediction'],
    data: function() {
        return {
            loading: true,
            stack: false
        };
    },
    methods: {
        getStatus() {
            this.loading = false;
        }
    }
}
</script>
