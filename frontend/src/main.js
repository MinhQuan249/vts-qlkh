import './assets/main.css'

import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";

const app = createApp(App);
app.use(router);
app.mount("#app"); // Đảm bảo chỉ gọi `mount` ở đây

import axios from 'axios';

axios.defaults.baseURL = 'http://localhost:8080'; // Địa chỉ của Spring Boot server