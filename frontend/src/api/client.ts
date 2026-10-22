/** Axios-based API client with base URL configuration. */

import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "";

const client = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.data?.error) {
      const apiError = error.response.data.error;
      return Promise.reject(
        new Error(apiError.message || "An unknown error occurred")
      );
    }
    return Promise.reject(error);
  }
);

export default client;
