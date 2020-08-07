<template>
    <div class='col col--12'>
        <div class='col col--12 clearfix py6'>
            <h2 class='fl cursor-default'>Models</h2>

            <div class='fr'>
                <label class='switch-container px6'>
                    <span class='mr6'>Archived</span>
                    <input v-model='archived' type='checkbox' />
                    <div class='switch'></div>
                </label>

                <button @click='showSearch = !showSearch' class='btn round btn--stroke color-gray color-blue-on-hover mr12'>
                    <svg class='icon'><use href='#icon-search'/></svg>
                </button>
                <button @click='refresh' class='btn round btn--stroke color-gray color-blue-on-hover mr12'>
                    <svg class='icon'><use href='#icon-refresh'/></svg>
                </button>
                <button @click='$router.push({ name: "newmodel" })' class='btn round btn--stroke color-gray color-green-on-hover'>
                    <svg class='icon'><use href='#icon-plus'/></svg>
                </button>
            </div>
        </div>
        <div class='border border--gray-light round mb60'>
            <template v-if='showSearch'>
                <div class='col col--12 px24 py6'>
                    <div class='relative'>
                        <div class='absolute flex-parent flex-parent--center-cross flex-parent--center-main w36 h36'>
                            <svg class='icon'><use xlink:href='#icon-search'></use></svg>
                        </div>
                        <input ref='search' v-model='search' class='input pl36' placeholder='Model Name'>
                    </div>
                </div>
            </template>
            <template v-if='models.length === 0'>
                <div class='flex-parent flex-parent--center-main pt36'>
                    <svg class='flex-child icon w60 h60 color--gray'><use href='#icon-info'/></svg>
                </div>

                <div class='flex-parent flex-parent--center-main pt12 pb36'>
                    <h1 class='flex-child txt-h4 cursor-default'>No Models Found</h1>
                </div>
            </template>
            <template v-else>
                <div @click='$router.push({ name: "model", params: { modelid: model.modelId } })' :key='model.modelId' v-for='model in models'>
                    <div class='cursor-pointer bg-darken10-on-hover col col--12 py12'>
                        <div class='col col--12 grid py6 px12'>
                            <div class='col col--6'>
                                <div class='col col--12 clearfix'>
                                    <h3 class='txt-h4 fl' v-text='model.name'></h3>
                                    <svg @click.prevent.stop='$router.push({ name: "editmodel", params: { modelid: model.modelId } })' class='fl my6 mx6 icon cursor-pointer color-gray-light color-gray-on-hover'><use href='#icon-pencil'/></svg>
                                </div>
                                <div class='col col--12'>
                                    <h3 class='txt-xs' v-text='model.source'></h3>
                                </div>
                            </div>
                            <div class='col col--6'>
                                <div @click.prevent.stop='external(model.projectUrl)' class='fr bg-blue-faint bg-blue-on-hover color-white-on-hover color-blue inline-block px6 py3 round txt-xs txt-bold cursor-pointer'>
                                    Project Page
                                </div>

                                <div v-if='stacks.models.includes(model.modelId)' class='fr bg-green-faint bg-green-on-hover color-white-on-hover color-green inline-block px6 py3 round txt-xs txt-bold mr3'>
                                    Active Stack
                                </div>
                                <div v-if='model.archived' class='fr bg-gray-faint bg-gray-on-hover color-white-on-hover color-gray inline-block px6 py3 round txt-xs txt-bold mr3'>
                                    Archived
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <Pager :total='models.length' perpage='10'/>
            </template>
        </div>
    </div>
</template>

<script>
import Pager from './util/Pager.vue';

export default {
    name: 'Home',
    props: ['meta', 'stacks'],
    data: function() {
        return {
            showSearch: false,
            search: '',
            archived: false,
            models: []
        }
    },
    mounted: function() {
        this.refresh();

        window.addEventListener('keydown', (e) => {
            if (e.keyCode === 114 || (e.ctrlKey && e.keyCode === 70)) {
                e.preventDefault();
                this.showSearch = true;
            } else if (e.keyCode === 27) {
                e.preventDefault();
                this.showSearch = false;
            }
        })
    },
    watch: {
        showSearch: function() {
            if (!this.showSearch) this.search = '';

            this.$nextTick(() => {
                if (this.showSearch) this.$refs.search.focus()
            });
        },
        search: function() {
            this.refresh();
        },
        archived: function() {
            this.refresh();
        }
    },
    methods: {
        refresh: function() {
            this.getModels();
        },
        external: function(url) {
            if (!url) return;
            window.open(url, "_blank")
        },
        getModels: async function() {
            try {
                const url = new URL(window.api + '/v1/model/all');
                url.searchParams.append('filter', this.search);
                url.searchParams.append('archived', this.archived);

                const res = await fetch(url, {
                    method: 'GET'
                });

                const body = await res.json();
                if (res.status === 404) {
                    this.models = [];
                } else if (!res.ok) {
                    throw new Error(body.message);
                } else {
                    this.models = body;
                }
            } catch (err) {
                this.$emit('err', err);
            }
        }
    },
    components: {
        Pager
    }
}
</script>
