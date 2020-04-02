import Vue from 'vue'
import VueRouter from  'vue-router'

import Model from './components/Model.vue';
import EditModel from './components/EditModel.vue';

Vue.use(VueRouter);

const router = new VueRouter({
    mode: 'history',
    routes: [
        { path: '/model/:model', name: 'model', component: Model },
        { path: '/model/:model/edit', name: 'editmodel', component: EditModel }
    ]
});

export default router
