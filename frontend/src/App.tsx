import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Contact from './pages/Contact';
import LandPrice from './pages/Predictions/LandPrice';
import HousePrice from './pages/Predictions/HousePrice';
import RentalPrice from './pages/Predictions/RentalPrice';
import LoginPage from './pages/LoginPage';
import Chatbot from './pages/Chatbot';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/chatbot" element={<Chatbot />} />
        
        {/* Prediction Routes */}
        <Route path="/land-price" element={<LandPrice />} />
        <Route path="/house-price" element={<HousePrice />} />
        <Route path="/rental-price" element={<RentalPrice />} />
      </Routes>
    </Router>
  );
}

export default App;