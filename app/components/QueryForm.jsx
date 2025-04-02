import React, { useState } from 'react';

/**
 * QueryForm component for legal questions
 * 
 * This component provides a form for users to submit legal questions,
 * with options for specifying the domain and additional context.
 */
const QueryForm = ({ onSubmit, isLoading }) => {
  const [formData, setFormData] = useState({
    query: '',
    domain: '',
    context: '',
  });

  const domains = [
    { value: '', label: 'Sélectionnez un domaine' },
    { value: 'fiscal', label: 'Droit Fiscal' },
    { value: 'travail', label: 'Droit du Travail' },
    { value: 'affaires', label: 'Droit des Affaires' },
    { value: 'famille', label: 'Droit de la Famille' },
    { value: 'immobilier', label: 'Droit Immobilier' },
    { value: 'consommation', label: 'Droit de la Consommation' },
    { value: 'penal', label: 'Droit Pénal' },
    { value: 'autre', label: 'Autre Domaine' },
  ];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validate query length
    if (formData.query.length < 10) {
      alert('Votre question est trop courte. Veuillez fournir plus de détails.');
      return;
    }
    
    onSubmit(formData);
  };

  return (
    <div className="query-form-container">
      <form onSubmit={handleSubmit} className="query-form">
        <h2>Posez votre question juridique</h2>
        
        <div className="form-group">
          <label htmlFor="domain">Domaine juridique</label>
          <select 
            id="domain" 
            name="domain" 
            value={formData.domain} 
            onChange={handleChange}
            className="form-control"
          >
            {domains.map(domain => (
              <option key={domain.value} value={domain.value}>
                {domain.label}
              </option>
            ))}
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="query">Votre question*</label>
          <textarea 
            id="query" 
            name="query" 
            value={formData.query} 
            onChange={handleChange}
            placeholder="Ex: Quelles sont les obligations d'un employeur lors d'un licenciement économique ?"
            rows={4}
            required
            minLength={10}
            maxLength={2000}
            className="form-control"
          />
          <small>{formData.query.length}/2000 caractères</small>
        </div>
        
        <div className="form-group">
          <label htmlFor="context">Contexte additionnel (facultatif)</label>
          <textarea 
            id="context" 
            name="context" 
            value={formData.context} 
            onChange={handleChange}
            placeholder="Fournissez des détails supplémentaires pour mieux contextualiser votre question..."
            rows={3}
            maxLength={5000}
            className="form-control"
          />
          <small>{formData.context.length}/5000 caractères</small>
        </div>
        
        <div className="form-actions">
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={isLoading || formData.query.length < 10}
          >
            {isLoading ? 'Analyse en cours...' : 'Obtenir une réponse'}
          </button>
        </div>
        
        <div className="form-disclaimer">
          <small>
            * Nos réponses sont fournies à titre informatif uniquement et ne constituent pas un avis juridique.
            Pour des situations complexes, veuillez consulter un professionnel du droit.
          </small>
        </div>
      </form>
    </div>
  );
};

export default QueryForm; 