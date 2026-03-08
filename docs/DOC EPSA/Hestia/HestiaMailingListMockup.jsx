import React, { useState } from 'react';

// Données de démo
const mockMailingLists = [
  { id: '1', name: 'ML-RH', email: 'ml-rh@epsa.com', members: 45, type: 'Distribution' },
  { id: '2', name: 'ML-IT-Support', email: 'ml-it-support@epsa.com', members: 12, type: 'Distribution' },
  { id: '3', name: 'ML-Direction', email: 'ml-direction@epsa.com', members: 8, type: 'Mail-enabled Security' },
  { id: '4', name: 'ML-Marketing', email: 'ml-marketing@epsa.com', members: 23, type: 'Distribution' },
];

const mockMembers = [
  { id: '1', nom: 'Williams', prenom: 'John', email: 'john.williams@epsa.com', type: 'Utilisateur', inherited: false },
  { id: '2', nom: 'Dupont', prenom: 'Marie', email: 'marie.dupont@epsa.com', type: 'Utilisateur', inherited: false },
  { id: '3', nom: 'Martin', prenom: 'Pierre', email: 'pierre.martin@epsa.com', type: 'Utilisateur', inherited: true },
  { id: '4', nom: 'GRP-Finance', prenom: '', email: 'grp-finance@epsa.com', type: 'Groupe', inherited: false },
  { id: '5', nom: 'Bernard', prenom: 'Sophie', email: 'sophie.bernard@epsa.com', type: 'Utilisateur', inherited: false },
];

const mockOwners = [
  { id: '1', nom: 'Danou', prenom: 'Yann', email: 'yann.danou@epsa.com' },
  { id: '2', nom: 'Monroig', prenom: 'Nicolas', email: 'nicolas.monroig@epsa.com' },
];

const mockParentGroups = [
  { id: '1', name: 'ML-All-France', email: 'ml-all-france@epsa.com', type: 'Distribution' },
  { id: '2', name: 'ML-Corporate', email: 'ml-corporate@epsa.com', type: 'Distribution' },
];

export default function HestiaMailingListMockup() {
  const [currentView, setCurrentView] = useState('search'); // search, detail
  const [activeTab, setActiveTab] = useState('properties');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedList, setSelectedList] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedMembers, setSelectedMembers] = useState([]);
  
  // Propriétés éditables
  const [editedName, setEditedName] = useState('');
  const [editedDescription, setEditedDescription] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  const filteredLists = mockMailingLists.filter(
    list => list.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            list.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSelectList = (list) => {
    setSelectedList(list);
    setEditedName(list.name);
    setEditedDescription('Liste de distribution pour le service ' + list.name.replace('ML-', ''));
    setCurrentView('detail');
    setActiveTab('properties');
    setHasChanges(false);
  };

  const handleBack = () => {
    setCurrentView('search');
    setSelectedList(null);
    setSearchQuery('');
  };

  const toggleMemberSelection = (id) => {
    setSelectedMembers(prev => 
      prev.includes(id) ? prev.filter(m => m !== id) : [...prev, id]
    );
  };

  const tabStyle = (isActive) => ({
    padding: '12px 24px',
    border: 'none',
    borderBottom: isActive ? '3px solid #4CAF50' : '3px solid transparent',
    background: 'transparent',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: isActive ? '600' : '400',
    color: isActive ? '#4CAF50' : '#666',
    transition: 'all 0.2s ease',
  });

  return (
    <div style={{ fontFamily: "'Segoe UI', Arial, sans-serif", background: '#F5F7FA', minHeight: '100vh' }}>
      {/* Header */}
      <header style={{ 
        background: 'white', 
        padding: '12px 32px', 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        borderBottom: '1px solid #E0E0E0',
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '28px', fontWeight: '700', color: '#2E7D32' }}>epsa</span>
          <span style={{ fontSize: '28px', color: '#FFD700' }}>*</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ color: '#666', fontSize: '14px' }}>lionel.tchamfong - Admin-Hestia</span>
          <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#E0E0E0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="#666"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '4px 8px', border: '1px solid #E0E0E0', borderRadius: '4px' }}>
            <span style={{ fontSize: '12px' }}>🇫🇷</span>
            <span style={{ fontSize: '12px' }}>FR</span>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav style={{ 
        background: 'white', 
        padding: '16px 32px',
        display: 'flex',
        gap: '12px',
        borderBottom: '1px solid #E0E0E0'
      }}>
        {[
          { icon: '→', label: "Liste d'Onboarding", active: false },
          { icon: '←', label: "Liste d'Offboarding", active: false },
          { icon: '👥', label: 'Gestion des collaborateurs', active: false },
          { icon: '✉️', label: 'Gestion des Mailing Lists', active: true },
          { icon: '⚙️', label: 'Paramétrage', active: false },
        ].map((item, idx) => (
          <button key={idx} style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 20px',
            border: item.active ? '2px solid #4CAF50' : '1px solid #E0E0E0',
            borderRadius: '25px',
            background: item.active ? '#E8F5E9' : 'white',
            cursor: 'pointer',
            fontSize: '14px',
            color: item.active ? '#2E7D32' : '#333',
            fontWeight: item.active ? '600' : '400',
            transition: 'all 0.2s ease',
          }}>
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      {/* Main Content */}
      <main style={{ padding: '32px', maxWidth: '1400px', margin: '0 auto' }}>
        
        {/* Vue Recherche */}
        {currentView === 'search' && (
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: '600', color: '#333', marginBottom: '24px' }}>
              Gestion des Mailing Lists
            </h1>
            
            {/* Barre de recherche */}
            <div style={{ 
              display: 'flex', 
              alignItems: 'center',
              background: 'white',
              borderRadius: '8px',
              padding: '12px 20px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
              marginBottom: '24px',
              maxWidth: '600px'
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="#999" style={{ marginRight: '12px' }}>
                <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
              </svg>
              <input
                type="text"
                placeholder="Rechercher une mailing list (nom ou email)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  flex: 1,
                  border: 'none',
                  outline: 'none',
                  fontSize: '14px',
                  color: '#333'
                }}
              />
            </div>

            {/* Résultats */}
            {searchQuery.length >= 2 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <p style={{ color: '#666', fontSize: '14px', marginBottom: '8px' }}>
                  {filteredLists.length} résultat(s) trouvé(s)
                </p>
                {filteredLists.map(list => (
                  <div 
                    key={list.id}
                    onClick={() => handleSelectList(list)}
                    style={{
                      background: 'white',
                      borderRadius: '8px',
                      padding: '16px 20px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                      border: '1px solid #E0E0E0',
                      transition: 'all 0.2s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = '#4CAF50';
                      e.currentTarget.style.boxShadow = '0 4px 12px rgba(76,175,80,0.15)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = '#E0E0E0';
                      e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.05)';
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      <div style={{ 
                        width: '44px', 
                        height: '44px', 
                        borderRadius: '50%', 
                        background: '#E3F2FD',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '20px'
                      }}>
                        ✉️
                      </div>
                      <div>
                        <div style={{ fontWeight: '600', fontSize: '15px', color: '#333' }}>{list.name}</div>
                        <div style={{ color: '#666', fontSize: '13px' }}>{list.email}</div>
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      <span style={{ 
                        background: '#E8F5E9', 
                        color: '#2E7D32', 
                        padding: '4px 12px', 
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: '500'
                      }}>
                        {list.members} membres
                      </span>
                      <span style={{ 
                        background: '#F5F5F5', 
                        color: '#666', 
                        padding: '4px 10px', 
                        borderRadius: '4px',
                        fontSize: '11px'
                      }}>
                        {list.type}
                      </span>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="#999">
                        <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
                      </svg>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {searchQuery.length < 2 && (
              <div style={{ 
                textAlign: 'center', 
                padding: '60px 20px',
                color: '#999'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
                <p>Saisissez au moins 2 caractères pour rechercher une mailing list</p>
              </div>
            )}
          </div>
        )}

        {/* Vue Détail */}
        {currentView === 'detail' && selectedList && (
          <div>
            {/* Header avec nom de la liste */}
            <div style={{ 
              background: 'white', 
              borderRadius: '8px', 
              padding: '20px 24px',
              marginBottom: '24px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <button 
                  onClick={handleBack}
                  style={{
                    background: 'none',
                    border: '1px solid #E0E0E0',
                    borderRadius: '8px',
                    padding: '8px 12px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    color: '#666',
                    fontSize: '13px'
                  }}
                >
                  ← Retour
                </button>
                <div style={{ 
                  width: '48px', 
                  height: '48px', 
                  borderRadius: '50%', 
                  background: '#E3F2FD',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '24px'
                }}>
                  ✉️
                </div>
                <div>
                  <h2 style={{ margin: 0, fontSize: '20px', fontWeight: '600', color: '#333' }}>{selectedList.name}</h2>
                  <p style={{ margin: '4px 0 0', color: '#666', fontSize: '14px' }}>{selectedList.email}</p>
                </div>
              </div>
              <span style={{ 
                background: '#E8F5E9', 
                color: '#2E7D32', 
                padding: '6px 16px', 
                borderRadius: '16px',
                fontSize: '13px',
                fontWeight: '500'
              }}>
                {selectedList.members} membres
              </span>
            </div>

            {/* Onglets */}
            <div style={{ 
              background: 'white', 
              borderRadius: '8px 8px 0 0',
              borderBottom: '1px solid #E0E0E0',
              display: 'flex'
            }}>
              <button onClick={() => setActiveTab('properties')} style={tabStyle(activeTab === 'properties')}>
                📋 Propriétés
              </button>
              <button onClick={() => setActiveTab('members')} style={tabStyle(activeTab === 'members')}>
                👥 Membres
              </button>
              <button onClick={() => setActiveTab('owners')} style={tabStyle(activeTab === 'owners')}>
                👤 Propriétaires
              </button>
              <button onClick={() => setActiveTab('membership')} style={tabStyle(activeTab === 'membership')}>
                🔗 Appartenance
              </button>
            </div>

            {/* Contenu des onglets */}
            <div style={{ 
              background: 'white', 
              borderRadius: '0 0 8px 8px',
              padding: '24px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
            }}>
              
              {/* Onglet Propriétés */}
              {activeTab === 'properties' && (
                <div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
                    <div>
                      <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: '#666', fontWeight: '500' }}>
                        Nom du groupe
                      </label>
                      <input 
                        type="text" 
                        value={editedName}
                        onChange={(e) => { setEditedName(e.target.value); setHasChanges(true); }}
                        style={{
                          width: '100%',
                          padding: '12px 16px',
                          border: '1px solid #E0E0E0',
                          borderRadius: '6px',
                          fontSize: '14px',
                          boxSizing: 'border-box'
                        }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: '#666', fontWeight: '500' }}>
                        Adresse e-mail
                      </label>
                      <input 
                        type="text" 
                        value={selectedList.email}
                        disabled
                        style={{
                          width: '100%',
                          padding: '12px 16px',
                          border: '1px solid #E0E0E0',
                          borderRadius: '6px',
                          fontSize: '14px',
                          background: '#F5F5F5',
                          color: '#999',
                          boxSizing: 'border-box'
                        }}
                      />
                    </div>
                    <div style={{ gridColumn: '1 / -1' }}>
                      <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: '#666', fontWeight: '500' }}>
                        Description
                      </label>
                      <textarea 
                        value={editedDescription}
                        onChange={(e) => { setEditedDescription(e.target.value); setHasChanges(true); }}
                        rows={3}
                        style={{
                          width: '100%',
                          padding: '12px 16px',
                          border: '1px solid #E0E0E0',
                          borderRadius: '6px',
                          fontSize: '14px',
                          resize: 'vertical',
                          boxSizing: 'border-box'
                        }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: '#666', fontWeight: '500' }}>
                        Type de groupe
                      </label>
                      <input 
                        type="text" 
                        value={selectedList.type}
                        disabled
                        style={{
                          width: '100%',
                          padding: '12px 16px',
                          border: '1px solid #E0E0E0',
                          borderRadius: '6px',
                          fontSize: '14px',
                          background: '#F5F5F5',
                          color: '#999',
                          boxSizing: 'border-box'
                        }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: '#666', fontWeight: '500' }}>
                        ID d'objet
                      </label>
                      <input 
                        type="text" 
                        value="959e3645-994b-40fe-8e7b-e627fcc47aa1"
                        disabled
                        style={{
                          width: '100%',
                          padding: '12px 16px',
                          border: '1px solid #E0E0E0',
                          borderRadius: '6px',
                          fontSize: '14px',
                          background: '#F5F5F5',
                          color: '#999',
                          fontFamily: 'monospace',
                          boxSizing: 'border-box'
                        }}
                      />
                    </div>
                  </div>

                  {/* Encart modifications */}
                  {hasChanges && (
                    <div style={{ 
                      background: '#FFF8E1', 
                      border: '1px solid #FFE082',
                      borderRadius: '6px',
                      padding: '12px 16px',
                      marginBottom: '20px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px'
                    }}>
                      <span style={{ fontSize: '18px' }}>⚠️</span>
                      <span style={{ color: '#F57C00', fontSize: '13px' }}>
                        Modifications en cours : Nom du groupe, Description
                      </span>
                    </div>
                  )}

                  {/* Boutons */}
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                    <button 
                      onClick={() => { setEditedName(selectedList.name); setHasChanges(false); }}
                      style={{
                        padding: '10px 20px',
                        border: '1px solid #E0E0E0',
                        borderRadius: '6px',
                        background: 'white',
                        cursor: 'pointer',
                        fontSize: '14px',
                        color: '#666'
                      }}
                    >
                      Annuler
                    </button>
                    <button 
                      disabled={!hasChanges}
                      style={{
                        padding: '10px 20px',
                        border: 'none',
                        borderRadius: '6px',
                        background: hasChanges ? '#4CAF50' : '#E0E0E0',
                        color: 'white',
                        cursor: hasChanges ? 'pointer' : 'not-allowed',
                        fontSize: '14px',
                        fontWeight: '500',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}
                    >
                      💾 Sauvegarder
                    </button>
                  </div>
                </div>
              )}

              {/* Onglet Membres */}
              {activeTab === 'members' && (
                <div>
                  {/* Barre d'actions */}
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginBottom: '20px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      <div style={{ 
                        display: 'flex', 
                        alignItems: 'center',
                        background: '#F5F5F5',
                        borderRadius: '6px',
                        padding: '8px 12px'
                      }}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="#999" style={{ marginRight: '8px' }}>
                          <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                        </svg>
                        <input
                          type="text"
                          placeholder="Filtrer les membres..."
                          style={{ border: 'none', outline: 'none', background: 'transparent', fontSize: '13px' }}
                        />
                      </div>
                      <span style={{ color: '#666', fontSize: '13px' }}>
                        {mockMembers.length} membres
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '12px' }}>
                      {selectedMembers.length > 0 && (
                        <button style={{
                          padding: '8px 16px',
                          border: '1px solid #EF5350',
                          borderRadius: '6px',
                          background: 'white',
                          color: '#EF5350',
                          cursor: 'pointer',
                          fontSize: '13px'
                        }}>
                          🗑️ Supprimer ({selectedMembers.length})
                        </button>
                      )}
                      <button 
                        onClick={() => setShowAddModal(true)}
                        style={{
                          padding: '8px 16px',
                          border: 'none',
                          borderRadius: '6px',
                          background: '#4CAF50',
                          color: 'white',
                          cursor: 'pointer',
                          fontSize: '13px',
                          fontWeight: '500'
                        }}
                      >
                        + Ajouter un membre
                      </button>
                    </div>
                  </div>

                  {/* Tableau des membres */}
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ background: '#F5F5F5' }}>
                        <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', color: '#666', fontWeight: '600', width: '40px' }}>
                          <input type="checkbox" />
                        </th>
                        <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', color: '#666', fontWeight: '600' }}>Nom</th>
                        <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', color: '#666', fontWeight: '600' }}>Prénom</th>
                        <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', color: '#666', fontWeight: '600' }}>Email</th>
                        <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', color: '#666', fontWeight: '600' }}>Type</th>
                        <th style={{ padding: '12px 16px', textAlign: 'center', fontSize: '12px', color: '#666', fontWeight: '600' }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {mockMembers.map(member => (
                        <tr key={member.id} style={{ borderBottom: '1px solid #E0E0E0' }}>
                          <td style={{ padding: '12px 16px' }}>
                            {!member.inherited && (
                              <input 
                                type="checkbox" 
                                checked={selectedMembers.includes(member.id)}
                                onChange={() => toggleMemberSelection(member.id)}
                              />
                            )}
                          </td>
                          <td style={{ padding: '12px 16px', fontSize: '14px' }}>{member.nom}</td>
                          <td style={{ padding: '12px 16px', fontSize: '14px' }}>{member.prenom}</td>
                          <td style={{ padding: '12px 16px', fontSize: '14px', color: '#666' }}>{member.email}</td>
                          <td style={{ padding: '12px 16px' }}>
                            <span style={{ 
                              background: member.type === 'Groupe' ? '#E3F2FD' : '#F5F5F5',
                              color: member.type === 'Groupe' ? '#1976D2' : '#666',
                              padding: '4px 8px',
                              borderRadius: '4px',
                              fontSize: '11px'
                            }}>
                              {member.type}
                            </span>
                            {member.inherited && (
                              <span style={{ 
                                background: '#FFF3E0',
                                color: '#E65100',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                fontSize: '11px',
                                marginLeft: '6px'
                              }}>
                                Hérité
                              </span>
                            )}
                          </td>
                          <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                            {!member.inherited ? (
                              <button style={{ 
                                background: 'none', 
                                border: 'none', 
                                cursor: 'pointer',
                                color: '#EF5350',
                                fontSize: '16px'
                              }}>
                                🗑️
                              </button>
                            ) : (
                              <span style={{ color: '#999', fontSize: '11px' }}>—</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Onglet Propriétaires */}
              {activeTab === 'owners' && (
                <div>
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginBottom: '20px'
                  }}>
                    <div style={{ 
                      background: '#E3F2FD', 
                      padding: '12px 16px', 
                      borderRadius: '6px',
                      fontSize: '13px',
                      color: '#1976D2'
                    }}>
                      ℹ️ Les propriétaires peuvent modifier les membres et les paramètres de la mailing list.
                    </div>
                    <button style={{
                      padding: '8px 16px',
                      border: 'none',
                      borderRadius: '6px',
                      background: '#4CAF50',
                      color: 'white',
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: '500'
                    }}>
                      + Ajouter un propriétaire
                    </button>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {mockOwners.map(owner => (
                      <div key={owner.id} style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '16px',
                        background: '#FAFAFA',
                        borderRadius: '6px',
                        border: '1px solid #E0E0E0'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <div style={{ 
                            width: '40px', 
                            height: '40px', 
                            borderRadius: '50%', 
                            background: '#4CAF50',
                            color: 'white',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: '600',
                            fontSize: '14px'
                          }}>
                            {owner.prenom[0]}{owner.nom[0]}
                          </div>
                          <div>
                            <div style={{ fontWeight: '500', fontSize: '14px' }}>{owner.prenom} {owner.nom}</div>
                            <div style={{ color: '#666', fontSize: '13px' }}>{owner.email}</div>
                          </div>
                        </div>
                        <button style={{ 
                          background: 'none', 
                          border: '1px solid #EF5350', 
                          borderRadius: '6px',
                          padding: '6px 12px',
                          cursor: 'pointer',
                          color: '#EF5350',
                          fontSize: '12px'
                        }}>
                          Retirer
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Onglet Appartenance */}
              {activeTab === 'membership' && (
                <div>
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginBottom: '20px'
                  }}>
                    <div style={{ 
                      background: '#FFF3E0', 
                      padding: '12px 16px', 
                      borderRadius: '6px',
                      fontSize: '13px',
                      color: '#E65100'
                    }}>
                      ⚠️ Cette mailing list est membre des groupes suivants. Les emails envoyés à ces groupes seront également reçus ici.
                    </div>
                    <button style={{
                      padding: '8px 16px',
                      border: 'none',
                      borderRadius: '6px',
                      background: '#4CAF50',
                      color: 'white',
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: '500'
                    }}>
                      + Ajouter à un groupe
                    </button>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {mockParentGroups.map(group => (
                      <div key={group.id} style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '16px',
                        background: '#FAFAFA',
                        borderRadius: '6px',
                        border: '1px solid #E0E0E0'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <div style={{ 
                            width: '40px', 
                            height: '40px', 
                            borderRadius: '50%', 
                            background: '#E3F2FD',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '18px'
                          }}>
                            📁
                          </div>
                          <div>
                            <div style={{ fontWeight: '500', fontSize: '14px' }}>{group.name}</div>
                            <div style={{ color: '#666', fontSize: '13px' }}>{group.email}</div>
                          </div>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <span style={{ 
                            background: '#F5F5F5',
                            color: '#666',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontSize: '11px'
                          }}>
                            {group.type}
                          </span>
                          <button style={{ 
                            background: 'none', 
                            border: '1px solid #EF5350', 
                            borderRadius: '6px',
                            padding: '6px 12px',
                            cursor: 'pointer',
                            color: '#EF5350',
                            fontSize: '12px'
                          }}>
                            Retirer
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Modal Ajout Membre */}
      {showAddModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'white',
            borderRadius: '12px',
            width: '500px',
            maxHeight: '80vh',
            overflow: 'hidden',
            boxShadow: '0 20px 40px rgba(0,0,0,0.2)'
          }}>
            <div style={{ 
              padding: '20px 24px', 
              borderBottom: '1px solid #E0E0E0',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <h3 style={{ margin: 0, fontSize: '18px' }}>Ajouter un membre</h3>
              <button 
                onClick={() => setShowAddModal(false)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '20px', color: '#999' }}
              >
                ✕
              </button>
            </div>
            <div style={{ padding: '24px' }}>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center',
                background: '#F5F5F5',
                borderRadius: '6px',
                padding: '12px 16px',
                marginBottom: '20px'
              }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="#999" style={{ marginRight: '12px' }}>
                  <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                </svg>
                <input
                  type="text"
                  placeholder="Rechercher un utilisateur ou un groupe..."
                  style={{ flex: 1, border: 'none', outline: 'none', background: 'transparent', fontSize: '14px' }}
                />
              </div>
              <div style={{ color: '#666', fontSize: '13px', marginBottom: '12px' }}>Résultats suggérés :</div>
              {[
                { name: 'Alice Martin', email: 'alice.martin@epsa.com' },
                { name: 'Bob Johnson', email: 'bob.johnson@epsa.com' },
                { name: 'GRP-Comptabilité', email: 'grp-compta@epsa.com' },
              ].map((item, idx) => (
                <div key={idx} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  border: '1px solid #E0E0E0',
                  marginBottom: '8px'
                }}>
                  <input type="checkbox" />
                  <div style={{ 
                    width: '36px', 
                    height: '36px', 
                    borderRadius: '50%', 
                    background: '#E0E0E0',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '14px'
                  }}>
                    {item.name.includes('GRP') ? '👥' : item.name[0]}
                  </div>
                  <div>
                    <div style={{ fontSize: '14px', fontWeight: '500' }}>{item.name}</div>
                    <div style={{ fontSize: '12px', color: '#666' }}>{item.email}</div>
                  </div>
                </div>
              ))}
            </div>
            <div style={{ 
              padding: '16px 24px', 
              borderTop: '1px solid #E0E0E0',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '12px'
            }}>
              <button 
                onClick={() => setShowAddModal(false)}
                style={{
                  padding: '10px 20px',
                  border: '1px solid #E0E0E0',
                  borderRadius: '6px',
                  background: 'white',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Annuler
              </button>
              <button style={{
                padding: '10px 20px',
                border: 'none',
                borderRadius: '6px',
                background: '#4CAF50',
                color: 'white',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}>
                Ajouter la sélection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
