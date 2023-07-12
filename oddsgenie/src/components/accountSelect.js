function AccountSelect(){
    return (
        <div className="h-1/2 p-10 sm:w-full lg:w-1/3">
            <img src={require('../img/oddsgenie_logo.png')} alt="OddsGenie Logo" className="lg:w-2/3 sm:w-1/2 mx-auto mb-16"/>
            <div className='flex justify-evenly '>
                <button className="p-5 border-2 border-white text-white w-32 text-center text-xl bg-black font-serif rounded-2xl hover:text-black hover:bg-white">Login</button>
                <button className="p-5 border-2 border-white text-white w-32 text-center text-xl bg-black font-serif rounded-2xl hover:text-black hover:bg-white">Signup</button>
            </div>        
        </div>
    );
    }


export default AccountSelect;