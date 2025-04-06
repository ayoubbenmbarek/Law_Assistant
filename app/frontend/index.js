import React from 'react';
import { createRoot } from 'react-dom/client';
import App from '../components/App';

// Point d'entrée de l'application React
const container = document.getElementById('root');
const root = createRoot(container);
root.render(<App />); 