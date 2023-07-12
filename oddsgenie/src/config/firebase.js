// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_SECRET,
  authDomain: "oddsgenie-d025d.firebaseapp.com",
  projectId: "oddsgenie-d025d",
  storageBucket: "oddsgenie-d025d.appspot.com",
  messagingSenderId: "704925395420",
  appId: "1:704925395420:web:8e0795c6e7e21acf1b8719",
  measurementId: "G-LKD2V17X7V"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);