import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import SimConfig from './pages/SimConfig.jsx';
import Results from './pages/Results.jsx';
import Progress from './pages/Progress.jsx';

export default function App() {
  return (
    <BrowserRouter>
      <nav>
        <Link to="/">Configure</Link> |{' '}
        <Link to="/results">Results</Link> |{' '}
        <Link to="/progress">Progress</Link>
      </nav>
      <Routes>
        <Route path="/" element={<SimConfig />} />
        <Route path="/results" element={<Results />} />
        <Route path="/progress" element={<Progress />} />
      </Routes>
    </BrowserRouter>
  );
}
