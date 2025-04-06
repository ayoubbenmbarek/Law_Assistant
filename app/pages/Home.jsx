import React, { useState } from 'react';
import axios from 'axios';
import QueryForm from '../components/QueryForm';
import LegalResponse from '../components/LegalResponse';
import { FaExclamationTriangle, FaCheck } from 'react-icons/fa';

const Home = () => {
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState(null);

  // Gérer la soumission du formulaire de requête
  const handleQuerySubmit = (data) => {
    setResponse(data);
    setError(null);
  };

  // Gérer les erreurs de requête
  const handleQueryError = (errorMessage) => {
    setError(errorMessage);
    setResponse(null);
    
    // Effacer le message d'erreur après 5 secondes
    setTimeout(() => {
      setError(null);
    }, 5000);
  };

  // Générer un PDF à partir de la réponse
  const handleGeneratePdf = async () => {
    try {
      setNotification({
        type: 'info',
        message: 'Génération du PDF en cours...'
      });
      
      const pdfResponse = await axios.post('/api/generate-pdf', { response }, {
        responseType: 'blob'
      });
      
      // Créer un lien pour télécharger le PDF
      const url = window.URL.createObjectURL(new Blob([pdfResponse.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'reponse-juridique.pdf');
      document.body.appendChild(link);
      link.click();
      
      // Nettoyer
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      setNotification({
        type: 'success',
        message: 'PDF généré avec succès'
      });
      
      // Effacer la notification après 3 secondes
      setTimeout(() => {
        setNotification(null);
      }, 3000);
    } catch (error) {
      console.error('Erreur lors de la génération du PDF:', error);
      setNotification({
        type: 'error',
        message: 'Erreur lors de la génération du PDF'
      });
      
      // Effacer la notification après 5 secondes
      setTimeout(() => {
        setNotification(null);
      }, 5000);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Assistant Juridique IA</h1>
        <p className="text-lg text-gray-600">
          Obtenez des réponses précises à vos questions juridiques
        </p>
      </header>

      {/* Notification */}
      {notification && (
        <div className={`mb-4 p-4 rounded-md ${
          notification.type === 'error' ? 'bg-red-50 text-red-700' : 
          notification.type === 'success' ? 'bg-green-50 text-green-700' : 
          'bg-blue-50 text-blue-700'
        }`}>
          <div className="flex items-center">
            {notification.type === 'success' ? (
              <FaCheck className="mr-2" />
            ) : (
              <FaExclamationTriangle className="mr-2" />
            )}
            <span>{notification.message}</span>
          </div>
        </div>
      )}

      {/* Erreur */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 text-red-700 rounded-md">
          <div className="flex items-center">
            <FaExclamationTriangle className="mr-2" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Composants principaux */}
      <div className="grid grid-cols-1 gap-8">
        {/* Formulaire de requête toujours visible */}
        <QueryForm onSubmit={handleQuerySubmit} onError={handleQueryError} />
        
        {/* Réponse juridique (conditionnelle) */}
        {response && (
          <LegalResponse response={response} onGeneratePdf={handleGeneratePdf} />
        )}
      </div>

      {/* Pied de page */}
      <footer className="mt-12 pt-6 border-t border-gray-200 text-center text-sm text-gray-500">
        <p className="mb-2">
          Les informations fournies par cet assistant sont à titre informatif uniquement et 
          ne constituent pas un avis juridique professionnel.
        </p>
        <p>
          © {new Date().getFullYear()} Assistant Juridique IA. Tous droits réservés.
        </p>
      </footer>
    </div>
  );
};

export default Home; 