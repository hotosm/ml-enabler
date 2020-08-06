<template>
    <div class='col col--12'>
        <template v-if='log'>
            <div class='col col--12 grid py12'>
                <div class='col col--2 pb6'>
                    <button @click='closelogs' class='btn btn--s round btn--stroke btn--gray'>
                        <svg class='icon'><use href='#icon-arrow-left'/></svg>
                    </button>
                </div>
                <div class='col col--8'>
                    <h2 class='w-full align-center txt-h5'>Task #<span v-text='log'/> Logs</h2>
                </div>
            </div>

            <template v-if='loading.logs'>
                <div class='flex-parent flex-parent--center-main w-full pt24'>
                    <div class='flex-child loading py24'></div>
                </div>
                <div class='flex-parent flex-parent--center-main w-full pb24'>
                    <div class='flex-child py24'>Loading Logs</div>
                </div>
            </template>
            <template v-else>
                <div v-for='line in logs' :key='line.id' v-text='line.message' class='cursor-pointer bg-darken10-on-hover'></div>
            </template>
        </template>
        <template v-else>
            <h2 class='w-full align-center txt-h4 py12'>Tasks</h2>

            <div class='col col--12 grid border-b border--gray-light'>
                <div class='col col--2'>Type</div>
                <div class='col col--2'>Status</div>
                <div class='col col--6'>Note</div>
                <div class='col col--2 clearfix pr6'>
                    <button @click='$emit("create")' class='btn btn--s fr round btn--stroke btn--gray color-green-on-hover'>
                        <svg class='icon'><use href='#icon-plus'/></svg>
                    </button>
                    <button @click='getTasks' class='mr6 btn btn--s fr round btn--stroke btn--gray color-green-on-hover'>
                        <svg class='icon'><use href='#icon-refresh'/></svg>
                    </button>

                    <div v-if='loading.tasks'>
                        <div class='loading loading--s'></div>
                    </div>
                </div>
            </div>
            <template v-if='loading.init'>
                <div class='flex-parent flex-parent--center-main w-full pt24'>
                    <div class='flex-child loading py24'></div>
                </div>
                <div class='flex-parent flex-parent--center-main w-full pb24'>
                    <div class='flex-child py24'>Loading Tasks</div>
                </div>
            </template>
            <template v-else>
                <div @click='getLogs(task.id)' :key='task.id' v-for='task in tasks' :class='{ "cursor-pointer": task.logs }' class='col col--12 grid py6 bg-gray-light-on-hover round'>
                    <div class='col col--2 px6' v-text='task.type'></div>
                    <template v-if='task._loading'>
                        <div class='col col--8 loading loading--s h24'></div>
                    </template>
                    <template v-else>
                        <div class='col col--2 px6' v-text='task.status'></div>
                        <div class='col col--6 px6' v-text='task.statusReason'></div>
                    </template>
                    <div class='col col--2 px6 clearfix'>
                        <button @click='deleteTask(task.id)' class='btn fr round btn--stroke btn--s btn--gray color-red-on-hover'>
                            <svg class='icon'><use href='#icon-trash'/></svg>
                        </button>
                        <div v-if='task.logs' class='fr bg-gray-faint color-gray inline-block px6 py3 round txt-xs txt-bold mr6'>
                            Logs
                        </div>

                    </div>
                </div>
            </template>
        </template>
    </div>
</template>

<script>
export default {
    name: 'Tasks',
    props: ['prediction'],
    data: function() {
        return {
            init: true,
            tasks: [],
            log: false,
            logs: [],
            looping: false,
            loading: {
                init: true,
                tasks: true,
                logs: false
            }
        }
    },
    mounted: function() {
        this.refresh();
    },
    methods: {
        closelogs: function() {
            this.logs = [];
            this.log = false;
        },
        loop: function() {
            setTimeout(() => {
                this.getTasks(true);
            }, 10000);
        },
        refresh: function() {
            this.getTasks();
        },
        external: function(url) {
            if (!url) return;

            window.open(url, "_blank")
        },
        getLogs: async function(task_id) {
            this.loading.logs = true;
            this.log = task_id;

            try {
                const res = await fetch(window.api + `/v1/task/${task_id}/logs`, {
                    method: 'GET'
                });

                const body = await res.json();
                if (!res.ok) throw new Error(body.message)

                this.logs = body.logs;
                this.loading.logs = false;
            } catch (err) {
                this.$emit('err', err);
            }
        },
        getTasks: async function(loop) {
            if (this.init) {
                this.init = false;
                this.loading.init = true;
            } else {
                this.loading.tasks = true;
            }

            try {
                const res = await fetch(window.api + `/v1/task?pred_id=${this.$route.params.predid}&type=retrain`, {
                    method: 'GET'
                });

                const body = await res.json();
                if (!res.ok) throw new Error(body.message)

                this.tasks = body.tasks.map((task) => {
                    task._loading = true;
                    return task;
                });
                this.tasks.forEach(task => this.getTask(task.id));

                this.loading.init = false;
                this.loading.tasks = false;
                if (loop) this.loop();
            } catch (err) {
                console.error(err)
                this.$emit('err', err);
            }
        },
        getTask: async function(task_id) {
            try {
                const res = await fetch(window.api + `/v1/task/${task_id}`, {
                    method: 'GET'
                });

                const body = await res.json();
                if (!res.ok) throw new Error(body.message)

                for (const task of this.tasks) {
                    if (task.id !== body.id) continue;
                    task.status = body.status;
                    task.statusReason = body.statusReason;
                    task.logs = body.logs;
                    task._loading = false;
                }
            } catch (err) {
                console.error(err)
                this.$emit('err', err);
            }
        },
        deleteTask: async function(task_id) {
            try {
                let res = await fetch(window.api + `/v1/task/${task_id}`, {
                    method: 'DELETE'
                });

                let body = await res.json();
                if (!res.ok) throw new Error(body.message)

                this.getTasks()
            } catch (err) {
                console.error(err)
                this.$emit('err', err);
            }
        },
    }
}
</script>
