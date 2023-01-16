// Import the functions you need from the SDKs you need
import { getAuth } from "@firebase/auth";
import { initializeApp } from "firebase/app";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCvIpNQrwrvD-rVwNdwxLt9IWhj-T21j-A",
  authDomain: "jnp-auth.firebaseapp.com",
  projectId: "jnp-auth",
  storageBucket: "jnp-auth.appspot.com",
  messagingSenderId: "655923409901",
  appId: "1:655923409901:web:a5a3e7c37472dcef24ade4"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);