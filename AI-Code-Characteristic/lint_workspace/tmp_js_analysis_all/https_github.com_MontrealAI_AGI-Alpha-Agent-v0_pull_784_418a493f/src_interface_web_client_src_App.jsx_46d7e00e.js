import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import SimConfig from './pages/SimConfig.jsx';
import Results from './pages/Results.jsx';
import Logs from './pages/Logs.jsx';

export default function App() {
  return (
    <BrowserRouter>
      <nav>
        <Link to="/">Configure</Link> |{' '}
        <Link to="/results">Results</Link> |{' '}
        <Link to="/logs">Logs</Link>
      </nav>
      <Routes>
        <Route path="/" element={<SimConfig />} />
        <Route path="/results" element={<Results />} />
        <Route path="/logs" element={<Logs />} />
      </Routes>
    </BrowserRouter>
  );
}
