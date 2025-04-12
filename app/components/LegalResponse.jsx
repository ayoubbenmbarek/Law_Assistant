import React, { useState } from 'react';
import { FaPrint, FaFilePdf, FaShareAlt, FaSearch, FaInfoCircle } from 'react-icons/fa';
import SourceViewer from './SourceViewer';
import SourceList from './SourceList';
import './LegalResponse.css';

/**
 * LegalResponse component for displaying legal responses
 * 
 * This component renders a structured legal response with sections for
 * introduction, legal framework, application, exceptions, recommendations,
 * and sources.
 */
const LegalResponse = ({ response, onGeneratePdf }) => {
  const [selectedSourceId, setSelectedSourceId] = useState(null);
  const [showSources, setShowSources] = useState(false);
  
  if (!response) return null;
  
  const {
    introduction,
    legal_framework,
    application,
    exceptions,
    recommendations,
    sources,
    date_updated,
    disclaimer
  } = response;

  // Vérifier si les sources sont des objets ou des chaînes de caractères
  const isSourcesObjects = sources && sources.length > 0 && typeof sources[0] === 'object';

  const handlePrint = () => {
    window.print();
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: 'Réponse juridique',
        text: introduction,
        url: window.location.href,
      })
      .catch((error) => console.error('Erreur lors du partage:', error));
    } else {
      alert('Le partage n\'est pas pris en charge par votre navigateur');
    }
  };

  // Afficher le SourceViewer si une source est sélectionnée
  if (selectedSourceId) {
    return (
      <SourceViewer 
        sourceId={selectedSourceId}
        onClose={() => setSelectedSourceId(null)}
      />
    );
  }

  return (
    <div className="bg-white shadow-md rounded-lg p-6 mb-6 print:shadow-none print:p-0">
      <div className="flex justify-between items-start mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Réponse Juridique</h2>
        <div className="flex space-x-2 print:hidden">
          <button 
            onClick={handlePrint}
            className="p-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            title="Imprimer"
          >
            <FaPrint />
          </button>
          <button 
            onClick={onGeneratePdf}
            className="p-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            title="Exporter en PDF"
          >
            <FaFilePdf />
          </button>
          <button 
            onClick={handleShare}
            className="p-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            title="Partager"
          >
            <FaShareAlt />
          </button>
        </div>
      </div>

      {/* Introduction */}
      <section className="mb-6">
        <h3 className="text-xl font-semibold mb-2 text-gray-700">Introduction</h3>
        <div className="text-gray-700">
          {introduction.split('\n').map((paragraph, index) => (
            <p key={index} className="mb-2">{paragraph}</p>
          ))}
        </div>
      </section>

      {/* Cadre juridique */}
      <section className="mb-6">
        <h3 className="text-xl font-semibold mb-2 text-gray-700">Cadre juridique</h3>
        <div className="text-gray-700">
          {legal_framework.split('\n').map((paragraph, index) => (
            <p key={index} className="mb-2">{paragraph}</p>
          ))}
        </div>
      </section>

      {/* Application pratique */}
      <section className="mb-6">
        <h3 className="text-xl font-semibold mb-2 text-gray-700">Application</h3>
        <div className="text-gray-700">
          {application.split('\n').map((paragraph, index) => (
            <p key={index} className="mb-2">{paragraph}</p>
          ))}
        </div>
      </section>

      {/* Exceptions (si présent) */}
      {exceptions && (
        <section className="mb-6">
          <h3 className="text-xl font-semibold mb-2 text-gray-700">Exceptions et cas particuliers</h3>
          <div className="text-gray-700">
            {exceptions.split('\n').map((paragraph, index) => (
              <p key={index} className="mb-2">{paragraph}</p>
            ))}
          </div>
        </section>
      )}

      {/* Recommandations */}
      <section className="mb-6">
        <h3 className="text-xl font-semibold mb-2 text-gray-700">Recommandations</h3>
        <ul className="list-disc list-inside text-gray-700 space-y-1 pl-4">
          {recommendations.map((recommendation, index) => (
            <li key={index} className="mb-1">{recommendation}</li>
          ))}
        </ul>
      </section>

      {/* Sources */}
      <section className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-xl font-semibold text-gray-700">Sources</h3>
          {isSourcesObjects && (
            <button 
              onClick={() => setShowSources(!showSources)} 
              className="text-sm text-indigo-600 hover:text-indigo-800 print:hidden"
            >
              {showSources ? 'Masquer les détails' : 'Afficher les détails'}
            </button>
          )}
        </div>
        
        {isSourcesObjects && showSources ? (
          <SourceList 
            sources={sources} 
            onSourceSelect={setSelectedSourceId}
            showTitle={false}
          />
        ) : (
          <ul className="list-disc list-inside text-gray-700 space-y-1 pl-4">
            {sources.map((source, index) => (
              <li key={index} className="mb-1 flex items-start">
                {isSourcesObjects ? (
                  <>
                    <span className="flex-1">{source.title} ({source.type})</span>
                    <button 
                      onClick={() => setSelectedSourceId(source.id)}
                      className="ml-2 text-indigo-600 hover:text-indigo-800 print:hidden"
                      title="Voir les détails"
                    >
                      <FaInfoCircle size={14} />
                    </button>
                  </>
                ) : (
                  <span className="flex-1">{source}</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Avertissement */}
      <section className="mb-4 mt-8 p-4 bg-gray-50 rounded-md border border-gray-200 text-sm text-gray-600 print:mt-4">
        <p className="font-medium mb-1">Avertissement :</p>
        <p>{disclaimer || "Cette réponse est générique et fournie à titre informatif uniquement. Elle ne constitue pas un avis juridique et ne doit pas se substituer à une consultation auprès d'un professionnel du droit."}</p>
        {date_updated && (
          <p className="mt-2 text-xs text-gray-500">
            Mis à jour le {new Date(date_updated).toLocaleDateString('fr-FR')}
          </p>
        )}
      </section>
    </div>
  );
};

export default LegalResponse; 