import React from 'react';

/**
 * LegalResponse component for displaying legal responses
 * 
 * This component renders a structured legal response with sections for
 * introduction, legal framework, application, exceptions, recommendations,
 * and sources.
 */
const LegalResponse = ({ response }) => {
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

  return (
    <div className="legal-response">
      <div className="response-header">
        <h2>Réponse Juridique</h2>
        <div className="date-updated">
          <small>Informations à jour au {date_updated}</small>
        </div>
      </div>
      
      <div className="response-content">
        <section className="response-section">
          <h3>Introduction</h3>
          <p>{introduction}</p>
        </section>
        
        <section className="response-section">
          <h3>Cadre Légal</h3>
          <p>{legal_framework}</p>
        </section>
        
        <section className="response-section">
          <h3>Application</h3>
          <p>{application}</p>
        </section>
        
        {exceptions && (
          <section className="response-section">
            <h3>Exceptions et Cas Particuliers</h3>
            <p>{exceptions}</p>
          </section>
        )}
        
        <section className="response-section">
          <h3>Recommandations</h3>
          <ul className="recommendations-list">
            {recommendations.map((recommendation, index) => (
              <li key={index}>{recommendation}</li>
            ))}
          </ul>
        </section>
        
        <section className="response-section">
          <h3>Sources</h3>
          <ul className="sources-list">
            {sources.map((source, index) => (
              <li key={index}>{source}</li>
            ))}
          </ul>
        </section>
      </div>
      
      <div className="response-disclaimer">
        <p><strong>Avertissement :</strong> {disclaimer}</p>
      </div>
      
      <div className="response-actions">
        <button className="btn btn-outline">Imprimer</button>
        <button className="btn btn-outline">Exporter en PDF</button>
        <button className="btn btn-outline">Partager</button>
      </div>
    </div>
  );
};

export default LegalResponse; 