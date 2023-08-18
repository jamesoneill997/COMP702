import React, {useState} from 'react';
import { createUserWithEmailAndPassword, signOut, signInWithEmailAndPassword} from 'firebase/auth';
import { auth } from '../config/firebase'
import { Redirect } from 'react-router-dom';

const DetailsForm = ({ form_type }) => {
    var [form_type, setFormType] = useState(form_type);
    const [email, setEmail, password, setPassword] = useState('');
    const [redirect, setRedirect] = useState(false);

    const signup = async (email, password) => {
        try{
            await createUserWithEmailAndPassword(auth, email, password)
            this.setState({ redirect: true });
        }catch(error){
            console.log(error);
        }
        
    }
    re
    const signIn = async (email, password) => {
        try {
          await signInWithEmailAndPassword(auth, email, password);
          this.setState({ redirect: true });
        } catch (err) {
          console.error(err);
          alert(err.message);
        }
      };

    return (
        <div className="fixed inset-0 flex justify-center items-center bg-black bg-opacity-50 z-50">
        <div className="bg-black text-white w-96 rounded-lg border-white border-2 p-6">
        <img src={require('../img/oddsgenie_logo.png')} alt="logo" className="w-80 mb-12 mx-auto mb-4" />
            <h2 className="text-2xl font-semibold mb-4">
            {form_type === 'login' ? 'Login' : 'Sign Up'}
            </h2>
            <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Username</label>
            <input
                type="text"
                className="w-full border rounded-md p-2 text-black"
                placeholder="Enter your username"
                onChange={(e)=>setEmail(e.target.value+ "@oddsgenie.app")}
            />
            </div>
            <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
                type="password"
                className="w-full border rounded-md p-2 text-black"
                placeholder="Enter your password"
                onChange={(e)=>setPassword(e.target.value)}
            />
            </div>
            <button 
            className="bg-blue-500 text-white rounded-lg py-2 px-4"
            onClick={form_type === 'login' ? () => signIn(email, password) : () => signup(email, password)}
            >
            {form_type === 'login' ? 'Login' : 'Sign Up'}
            </button>
            <p className='float-right w-1/2 text-right'>
                {form_type === 'login' ? "Don't have an account?" : "Have an account?"}
                <button className='font-bold text-blue-600 p-2' 
                    onClick={() => 
                        form_type === 'signup' ? setFormType('login') : setFormType('signup')
                    }>
                    {form_type === 'login' ? "Signup" : "Login"}

                </button>
            </p>
        </div>
        </div>
    );
    };

export default DetailsForm;