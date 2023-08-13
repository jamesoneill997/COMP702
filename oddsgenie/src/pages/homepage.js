import Auth from '../components/auth';
import AccountSelect from '../components/accountSelect';

function Homepage() {
	return (
        <div className="OddsGenie bg-[url('/public/homepage_background.jpg')] h-screen bg-cover">
            <div className="bg-black h-full bg-cover bg-opacity-80 flex justify-center items-center">
                <AccountSelect/>
                <Auth/>
            </div>
        </div>
	);
}

export default Homepage;