import React from 'react';
import './App.css';
import { BrowserRouter as Router, Routes, Route }
	from 'react-router-dom';
import HomePage from './pages/homepage';
import Predictions from './pages/predictions';
import Results from './pages/results';

function App() {
	return (
		<Router>
			<Routes>
				<Route exact path='/' element={<HomePage />} />
				<Route path='/predictions' element={<Predictions />} />
				<Route path='/results' element={<Results />} />
			</Routes>
		</Router>
	);
}

export default App;
