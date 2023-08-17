import React, {useState} from 'react';
import DetailsForm from './detailsForm';
function AccountSelect(){
    const [showForm, setShowForm] = useState(false);
    const [formType, setFormType] = useState('');
  
    const handleButtonClick = (type) => {
      setShowForm(true);
      setFormType(type);
    };
  
    const handleCloseForm = () => {
      setShowForm(false);
    };
    return (
        <div className="h-1/2 p-10 sm:w-full lg:w-1/3">
          <img
            src={require('../img/oddsgenie_logo.png')}
            alt="OddsGenie Logo"
            className="lg:w-2/3 sm:w-1/2 mx-auto mb-16"
          />
          <div className="flex justify-evenly">
            <button
              onClick={() => handleButtonClick('login')}
              className="p-5 border-2 border-white text-white w-32 text-center text-xl bg-black font-serif rounded-2xl hover:text-black hover:bg-white"
            >
              Login
            </button>
            <button
              onClick={() => handleButtonClick('signup')}
              className="p-5 border-2 border-white text-white w-32 text-center text-xl bg-black font-serif rounded-2xl hover:text-black hover:bg-white"
            >
              Signup
            </button>
          </div>
          {showForm && (
            <DetailsForm form_type={formType} onClose={handleCloseForm} />
          )}
        </div>
      );
    };


export default AccountSelect;