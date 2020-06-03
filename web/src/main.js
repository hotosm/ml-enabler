import Vue from 'vue'
import VueRouter from  'vue-router'

import App from './App.vue'

import Home from './components/Home.vue';
import Model from './components/Model.vue';
import EditModel from './components/EditModel.vue';

Vue.use(VueRouter);
Vue.config.productionTip = false

const router = new VueRouter({
    mode: 'history',
    routes: [
        { path: '/admin/', name: 'home', component: Home },
        { path: '/admin/model/new', name: 'newmodel', component: Model },
        { path: '/admin/model/:model', name: 'model', component: Model },
        { path: '/admin/model/:model/edit', name: 'editmodel', component: EditModel }
    ]
});

window.api = window.location.pathname.replace(/\/admin\/.*/, '');

new Vue({
    router,
    render: h => h(App)
}).$mount('#app')
