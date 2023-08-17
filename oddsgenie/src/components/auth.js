import { auth } from '../config/firebase'
import { createUserWithEmailAndPassword, signOut} from 'firebase/auth';
import { useState } from 'react';
import {DetailsForm} from './detailsForm'

const Auth = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    console.log(auth?.currentUser?.email);
    const login = async () => {
        try{
            await createUserWithEmailAndPassword(auth, email, password)
        }catch(error){
            console.log(error);
        }
    }

    const logout = async () => {
        try{
            await signOut(auth);
        }catch(error){
            console.log(error);
        }
    }
    return (
        <div>
            <div className='hidden'>
                <input 
                placeholder="Username"
                onChange={(e)=>setEmail(e.target.value+ "@oddsgenie.app")}
                />
                <input 
                placeholder="Password"
                type="password"
                onChange={(e)=>setPassword(e.target.value)}
                />
                <button className='text-lg' onClick={login}>Login</button>
                <button onClick={logout}>Logout</button>
            </div>
        </div>
    );
    }


export default Auth