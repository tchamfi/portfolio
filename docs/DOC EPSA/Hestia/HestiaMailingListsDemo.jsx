import React, { useState } from 'react';

// ============================================
// MOCK DATA
// ============================================
const mockMailingLists = [
  { id: '1', name: 'ML-RH', email: 'ml-rh@epsa.com', description: 'Liste de distribution pour le service Ressources Humaines', type: 'Distribution', membersCount: 45, objectId: '959e3645-994b-40fe-8e7b-e627fcc47aa1' },
  { id: '2', name: 'ML-IT-Support', email: 'ml-it-support@epsa.com', description: 'Liste de distribution pour le support informatique', type: 'Distribution', membersCount: 12, objectId: 'a1b2c3d4-5678-90ab-cdef-1234567890ab' },
  { id: '3', name: 'ML-Direction', email: 'ml-direction@epsa.com', description: 'Liste de distribution pour la direction générale', type: 'Distribution', membersCount: 8, objectId: 'b2c3d4e5-6789-01bc-def0-2345678901bc' },
  { id: '4', name: 'ML-Marketing', email: 'ml-marketing@epsa.com', description: 'Liste de distribution pour le service Marketing et Communication', type: 'Distribution', membersCount: 23, objectId: 'c3d4e5f6-7890-12cd-ef01-3456789012cd' },
  { id: '5', name: 'ML-Finance', email: 'ml-finance@epsa.com', description: 'Liste de distribution pour le service Finance et Comptabilité', type: 'Distribution', membersCount: 15, objectId: 'd4e5f6a7-8901-23de-f012-4567890123de' },
  { id: '6', name: 'ML-Commercial', email: 'ml-commercial@epsa.com', description: 'Liste de distribution pour les équipes commerciales', type: 'Distribution', membersCount: 67, objectId: 'e5f6a7b8-9012-34ef-0123-5678901234ef' },
  { id: '7', name: 'ML-Juridique', email: 'ml-juridique@epsa.com', description: 'Liste de distribution pour le service Juridique', type: 'Distribution', membersCount: 6, objectId: 'f6a7b8c9-0123-45f0-1234-6789012345f0' },
  { id: '8', name: 'ML-All-France', email: 'ml-all-france@epsa.com', description: 'Liste de distribution pour tous les collaborateurs France', type: 'Distribution', membersCount: 234, objectId: 'a7b8c9d0-1234-5601-2345-7890123456a1' },
];

const mockMembers = [
  { id: '1', nom: 'Williams', prenom: 'John', email: 'john.williams@epsa.com', type: 'Utilisateur', inherited: false },
  { id: '2', nom: 'Dupont', prenom: 'Marie', email: 'marie.dupont@epsa.com', type: 'Utilisateur', inherited: false },
  { id: '3', nom: 'Martin', prenom: 'Pierre', email: 'pierre.martin@epsa.com', type: 'Utilisateur', inherited: true, inheritedFrom: 'GRP-Finance' },
  { id: '4', nom: 'GRP-Finance', prenom: '', email: 'grp-finance@epsa.com', type: 'Groupe', inherited: false },
  { id: '5', nom: 'Bernard', prenom: 'Sophie', email: 'sophie.bernard@epsa.com', type: 'Utilisateur', inherited: false },
  { id: '6', nom: 'Lefebvre', prenom: 'Antoine', email: 'antoine.lefebvre@epsa.com', type: 'Utilisateur', inherited: false },
  { id: '7', nom: 'Moreau', prenom: 'Julie', email: 'julie.moreau@epsa.com', type: 'Utilisateur', inherited: true, inheritedFrom: 'GRP-Finance' },
  { id: '8', nom: 'Garcia', prenom: 'Lucas', email: 'lucas.garcia@epsa.com', type: 'Utilisateur', inherited: false },
];

const mockOwners = [
  { id: '1', nom: 'Danou', prenom: 'Yann', email: 'yann.danou@epsa.com' },
  { id: '2', nom: 'Monroig', prenom: 'Nicolas', email: 'nicolas.monroig@epsa.com' },
];

const mockParentGroups = [
  { id: '1', name: 'ML-All-France', email: 'ml-all-france@epsa.com', type: 'Distribution' },
  { id: '2', name: 'ML-Corporate', email: 'ml-corporate@epsa.com', type: 'Distribution' },
];

const mockSearchResults = [
  { id: '10', name: 'Alice Martin', email: 'alice.martin@epsa.com', type: 'Utilisateur' },
  { id: '11', name: 'Bob Johnson', email: 'bob.johnson@epsa.com', type: 'Utilisateur' },
  { id: '12', name: 'Claire Dubois', email: 'claire.dubois@epsa.com', type: 'Utilisateur' },
  { id: '13', name: 'GRP-Comptabilité', email: 'grp-compta@epsa.com', type: 'Groupe' },
  { id: '14', name: 'David Petit', email: 'david.petit@epsa.com', type: 'Utilisateur' },
  { id: '15', name: 'Emma Leroy', email: 'emma.leroy@epsa.com', type: 'Utilisateur' },
];

// ============================================
// ICONS (SVG)
// ============================================
const SearchIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="#999">
    <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
  </svg>
);

const ChevronIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="#999">
    <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
  </svg>
);

const UserIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="#666">
    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
  </svg>
);

// ============================================
// HEADER COMPONENT
// ============================================
const Header = () => (
  <header style={styles.header}>
    <div style={styles.headerLogo}>
      <span style={styles.logoText}>epsa</span>
      <span style={styles.logoStar}>*</span>
    </div>
    <div style={styles.headerUser}>
      <span style={styles.userName}>lionel.tchamfong - Admin-Hestia</span>
      <div style={styles.userAvatar}><UserIcon /></div>
      <div style={styles.langSelector}>
        <span>🇫🇷</span>
        <span style={styles.langCode}>FR</span>
      </div>
    </div>
  </header>
);

// ============================================
// NAVIGATION COMPONENT
// ============================================
const Navigation = ({ activeItem }) => {
  const navItems = [
    { id: 'onboarding', icon: '→', label: "Liste d'Onboarding" },
    { id: 'offboarding', icon: '←', label: "Liste d'Offboarding" },
    { id: 'collaborateurs', icon: '👥', label: 'Gestion des collaborateurs' },
    { id: 'mailing-lists', icon: '✉️', label: 'Gestion des Mailing Lists' },
    { id: 'parametrage', icon: '⚙️', label: 'Paramétrage' },
  ];

  return (
    <nav style={styles.navigation}>
      {navItems.map(item => (
        <button
          key={item.id}
          style={{
            ...styles.navBtn,
            ...(item.id === activeItem ? styles.navBtnActive : {})
          }}
        >
          <span>{item.icon}</span>
          <span>{item.label}</span>
        </button>
      ))}
    </nav>
  );
};

// ============================================
// SEARCH PAGE COMPONENT
// ============================================
const SearchPage = ({ onSelect }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = (value) => {
    setQuery(value);
    if (value.length >= 2) {
      setIsLoading(true);
      setTimeout(() => {
        const filtered = mockMailingLists.filter(
          ml => ml.name.toLowerCase().includes(value.toLowerCase()) ||
                ml.email.toLowerCase().includes(value.toLowerCase())
        );
        setResults(filtered);
        setIsLoading(false);
      }, 300);
    } else {
      setResults([]);
    }
  };

  return (
    <div style={styles.searchPage}>
      <h1 style={styles.pageTitle}>Gestion des Mailing Lists</h1>
      
      <div style={styles.searchBar}>
        <SearchIcon />
        <input
          type="text"
          style={styles.searchInput}
          placeholder="Rechercher une mailing list (nom ou email)..."
          value={query}
          onChange={(e) => handleSearch(e.target.value)}
        />
        {isLoading && <div style={styles.loader}></div>}
      </div>

      {query.length >= 2 ? (
        <div style={styles.resultsContainer}>
          <p style={styles.resultsCount}>{results.length} résultat(s) trouvé(s)</p>
          
          {results.length > 0 ? (
            <div style={styles.resultsList}>
              {results.map(ml => (
                <div
                  key={ml.id}
                  style={styles.resultCard}
                  onClick={() => onSelect(ml)}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#4CAF50';
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(76, 175, 80, 0.15)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = '#E0E0E0';
                    e.currentTarget.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.05)';
                  }}
                >
                  <div style={styles.resultLeft}>
                    <div style={styles.resultIcon}>✉️</div>
                    <div style={styles.resultInfo}>
                      <div style={styles.resultName}>{ml.name}</div>
                      <div style={styles.resultEmail}>{ml.email}</div>
                    </div>
                  </div>
                  <div style={styles.resultRight}>
                    <span style={styles.badgeMembers}>{ml.membersCount} membres</span>
                    <span style={styles.badgeType}>{ml.type}</span>
                    <ChevronIcon />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={styles.emptyState}>
              <div style={styles.emptyIcon}>🔍</div>
              <p>Aucune mailing list trouvée</p>
            </div>
          )}
        </div>
      ) : (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>🔍</div>
          <p>Saisissez au moins 2 caractères pour rechercher une mailing list</p>
        </div>
      )}
    </div>
  );
};

// ============================================
// DETAIL PAGE COMPONENT
// ============================================
const DetailPage = ({ mailingList, onBack }) => {
  const [activeTab, setActiveTab] = useState('properties');

  const tabs = [
    { id: 'properties', icon: '📋', label: 'Propriétés' },
    { id: 'members', icon: '👥', label: 'Membres' },
    { id: 'owners', icon: '👤', label: 'Propriétaires' },
    { id: 'membership', icon: '🔗', label: 'Appartenance' },
  ];

  return (
    <div style={styles.detailPage}>
      {/* Header */}
      <div style={styles.detailHeader}>
        <div style={styles.headerLeft}>
          <button style={styles.btnBack} onClick={onBack}>← Retour</button>
          <div style={styles.mlIcon}>✉️</div>
          <div style={styles.mlInfo}>
            <h2 style={styles.mlName}>{mailingList.name}</h2>
            <p style={styles.mlEmail}>{mailingList.email}</p>
          </div>
        </div>
        <span style={styles.badgeMembersLg}>{mailingList.membersCount} membres</span>
      </div>

      {/* Tabs */}
      <div style={styles.tabsBar}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            style={{
              ...styles.tab,
              ...(activeTab === tab.id ? styles.tabActive : {})
            }}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div style={styles.tabContent}>
        {activeTab === 'properties' && <PropertiesTab mailingList={mailingList} />}
        {activeTab === 'members' && <MembersTab />}
        {activeTab === 'owners' && <OwnersTab />}
        {activeTab === 'membership' && <MembershipTab />}
      </div>
    </div>
  );
};

// ============================================
// PROPERTIES TAB
// ============================================
const PropertiesTab = ({ mailingList }) => {
  const [name, setName] = useState(mailingList.name);
  const [description, setDescription] = useState(mailingList.description);
  const [isSaving, setIsSaving] = useState(false);

  const hasChanges = name !== mailingList.name || description !== mailingList.description;
  const changedFields = [];
  if (name !== mailingList.name) changedFields.push('Nom du groupe');
  if (description !== mailingList.description) changedFields.push('Description');

  const handleSave = () => {
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      alert('Modifications sauvegardées !');
    }, 500);
  };

  const handleCancel = () => {
    setName(mailingList.name);
    setDescription(mailingList.description);
  };

  return (
    <div style={styles.propertiesForm}>
      <div style={styles.formGrid}>
        <div style={styles.formGroup}>
          <label style={styles.formLabel}>Nom du groupe</label>
          <input
            type="text"
            style={styles.formInput}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div style={styles.formGroup}>
          <label style={styles.formLabel}>Adresse e-mail</label>
          <input
            type="text"
            style={{...styles.formInput, ...styles.formInputReadonly}}
            value={mailingList.email}
            disabled
          />
        </div>
        <div style={{...styles.formGroup, gridColumn: '1 / -1'}}>
          <label style={styles.formLabel}>Description</label>
          <textarea
            style={styles.formTextarea}
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        <div style={styles.formGroup}>
          <label style={styles.formLabel}>Type de groupe</label>
          <input
            type="text"
            style={{...styles.formInput, ...styles.formInputReadonly}}
            value={mailingList.type}
            disabled
          />
        </div>
        <div style={styles.formGroup}>
          <label style={styles.formLabel}>ID d'objet</label>
          <input
            type="text"
            style={{...styles.formInput, ...styles.formInputReadonly, fontFamily: 'monospace', fontSize: '12px'}}
            value={mailingList.objectId}
            disabled
          />
        </div>
      </div>

      {hasChanges && (
        <div style={styles.alertChanges}>
          <span>⚠️</span>
          <span>Modifications en cours : {changedFields.join(', ')}</span>
        </div>
      )}

      <div style={styles.formActions}>
        <button
          style={{...styles.btn, ...styles.btnSecondary, opacity: hasChanges ? 1 : 0.5}}
          disabled={!hasChanges}
          onClick={handleCancel}
        >
          Annuler
        </button>
        <button
          style={{...styles.btn, ...styles.btnPrimary, opacity: hasChanges && !isSaving ? 1 : 0.5}}
          disabled={!hasChanges || isSaving}
          onClick={handleSave}
        >
          💾 Sauvegarder
        </button>
      </div>
    </div>
  );
};

// ============================================
// MEMBERS TAB
// ============================================
const MembersTab = () => {
  const [filter, setFilter] = useState('');
  const [selectedIds, setSelectedIds] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [memberToRemove, setMemberToRemove] = useState(null);

  const filteredMembers = mockMembers.filter(m =>
    m.nom.toLowerCase().includes(filter.toLowerCase()) ||
    m.prenom.toLowerCase().includes(filter.toLowerCase()) ||
    m.email.toLowerCase().includes(filter.toLowerCase())
  );

  const toggleSelect = (id) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter(i => i !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const handleRemove = (member) => {
    setMemberToRemove(member);
    setShowConfirmModal(true);
  };

  return (
    <div>
      <div style={styles.actionsBar}>
        <div style={styles.actionsLeft}>
          <div style={styles.filterInput}>
            <SearchIcon />
            <input
              type="text"
              placeholder="Filtrer les membres..."
              style={styles.filterInputField}
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
          </div>
          <span style={styles.membersCount}>{filteredMembers.length} membres</span>
        </div>
        <div style={styles.actionsRight}>
          {selectedIds.length > 0 && (
            <button style={{...styles.btn, ...styles.btnDanger}}>
              🗑️ Supprimer ({selectedIds.length})
            </button>
          )}
          <button style={{...styles.btn, ...styles.btnPrimary}} onClick={() => setShowAddModal(true)}>
            + Ajouter un membre
          </button>
        </div>
      </div>

      <table style={styles.table}>
        <thead>
          <tr>
            <th style={{...styles.th, width: '40px'}}></th>
            <th style={styles.th}>Nom</th>
            <th style={styles.th}>Prénom</th>
            <th style={styles.th}>Email</th>
            <th style={styles.th}>Type</th>
            <th style={{...styles.th, width: '80px', textAlign: 'center'}}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {filteredMembers.map(member => (
            <tr key={member.id}>
              <td style={styles.td}>
                {!member.inherited && (
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(member.id)}
                    onChange={() => toggleSelect(member.id)}
                  />
                )}
              </td>
              <td style={styles.td}>{member.nom}</td>
              <td style={styles.td}>{member.prenom}</td>
              <td style={{...styles.td, color: '#666'}}>{member.email}</td>
              <td style={styles.td}>
                <span style={member.type === 'Groupe' ? styles.badgeGroup : styles.badgeUser}>
                  {member.type}
                </span>
                {member.inherited && (
                  <span style={styles.badgeInherited} title={`Hérité de ${member.inheritedFrom}`}>
                    Hérité
                  </span>
                )}
              </td>
              <td style={{...styles.td, textAlign: 'center'}}>
                {!member.inherited ? (
                  <button
                    style={styles.btnIcon}
                    onClick={() => handleRemove(member)}
                    title="Supprimer"
                  >
                    🗑️
                  </button>
                ) : (
                  <span style={{color: '#999'}} title={`Ce membre est hérité du groupe ${member.inheritedFrom}. Retirez-le du groupe parent pour le supprimer.`}>
                    —
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Add Modal */}
      {showAddModal && (
        <AddMemberModal onClose={() => setShowAddModal(false)} />
      )}

      {/* Confirm Modal */}
      {showConfirmModal && (
        <ConfirmModal
          title="Confirmer la suppression"
          message={`Êtes-vous sûr de vouloir retirer ${memberToRemove?.prenom} ${memberToRemove?.nom} de cette mailing list ?`}
          onConfirm={() => {
            setShowConfirmModal(false);
            setMemberToRemove(null);
          }}
          onCancel={() => {
            setShowConfirmModal(false);
            setMemberToRemove(null);
          }}
        />
      )}
    </div>
  );
};

// ============================================
// OWNERS TAB
// ============================================
const OwnersTab = () => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [ownerToRemove, setOwnerToRemove] = useState(null);

  return (
    <div>
      <div style={styles.alertInfo}>
        <span>ℹ️</span>
        <span>Les propriétaires peuvent modifier les membres et les paramètres de cette mailing list.</span>
      </div>

      <div style={styles.actionsBar}>
        <span style={styles.membersCount}>{mockOwners.length} propriétaire(s)</span>
        <button style={{...styles.btn, ...styles.btnPrimary}} onClick={() => setShowAddModal(true)}>
          + Ajouter un propriétaire
        </button>
      </div>

      <div style={styles.ownersList}>
        {mockOwners.map(owner => (
          <div key={owner.id} style={styles.ownerCard}>
            <div style={styles.ownerLeft}>
              <div style={styles.ownerAvatar}>
                {owner.prenom.charAt(0)}{owner.nom.charAt(0)}
              </div>
              <div style={styles.ownerInfo}>
                <div style={styles.ownerName}>{owner.prenom} {owner.nom}</div>
                <div style={styles.ownerEmail}>{owner.email}</div>
              </div>
            </div>
            <button
              style={{
                ...styles.btn,
                ...styles.btnOutlineDanger,
                opacity: mockOwners.length <= 1 ? 0.5 : 1
              }}
              disabled={mockOwners.length <= 1}
              title={mockOwners.length <= 1 ? 'Impossible de supprimer le dernier propriétaire' : 'Retirer ce propriétaire'}
              onClick={() => {
                setOwnerToRemove(owner);
                setShowConfirmModal(true);
              }}
            >
              Retirer
            </button>
          </div>
        ))}
      </div>

      {showAddModal && <AddMemberModal onClose={() => setShowAddModal(false)} title="Ajouter un propriétaire" />}
      
      {showConfirmModal && (
        <ConfirmModal
          title="Confirmer le retrait"
          message={`Êtes-vous sûr de vouloir retirer ${ownerToRemove?.prenom} ${ownerToRemove?.nom} des propriétaires de cette mailing list ?`}
          onConfirm={() => {
            setShowConfirmModal(false);
            setOwnerToRemove(null);
          }}
          onCancel={() => {
            setShowConfirmModal(false);
            setOwnerToRemove(null);
          }}
        />
      )}
    </div>
  );
};

// ============================================
// MEMBERSHIP TAB
// ============================================
const MembershipTab = () => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [groupToRemove, setGroupToRemove] = useState(null);

  return (
    <div>
      <div style={styles.alertWarning}>
        <span>⚠️</span>
        <span>Cette mailing list est membre des groupes suivants. Les emails envoyés à ces groupes seront également reçus ici.</span>
      </div>

      <div style={styles.actionsBar}>
        <span style={styles.membersCount}>{mockParentGroups.length} groupe(s) parent(s)</span>
        <button style={{...styles.btn, ...styles.btnPrimary}} onClick={() => setShowAddModal(true)}>
          + Ajouter à un groupe
        </button>
      </div>

      <div style={styles.ownersList}>
        {mockParentGroups.map(group => (
          <div key={group.id} style={styles.ownerCard}>
            <div style={styles.ownerLeft}>
              <div style={{...styles.ownerAvatar, background: '#E3F2FD', color: '#333'}}>📁</div>
              <div style={styles.ownerInfo}>
                <div style={styles.ownerName}>{group.name}</div>
                <div style={styles.ownerEmail}>{group.email}</div>
              </div>
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
              <span style={styles.badgeType}>{group.type}</span>
              <button
                style={{...styles.btn, ...styles.btnOutlineDanger}}
                onClick={() => {
                  setGroupToRemove(group);
                  setShowConfirmModal(true);
                }}
              >
                Retirer
              </button>
            </div>
          </div>
        ))}
      </div>

      {showAddModal && <AddMemberModal onClose={() => setShowAddModal(false)} title="Ajouter à un groupe" groupsOnly />}
      
      {showConfirmModal && (
        <ConfirmModal
          title="Confirmer le retrait"
          message={
            <div>
              <div style={styles.alertWarning}>
                <span>⚠️</span>
                <span>Attention : En retirant cette mailing list du groupe <strong>{groupToRemove?.name}</strong>, ses membres ne recevront plus les emails envoyés à ce groupe.</span>
              </div>
              <p style={{marginTop: '16px'}}>Voulez-vous continuer ?</p>
            </div>
          }
          onConfirm={() => {
            setShowConfirmModal(false);
            setGroupToRemove(null);
          }}
          onCancel={() => {
            setShowConfirmModal(false);
            setGroupToRemove(null);
          }}
          danger
        />
      )}
    </div>
  );
};

// ============================================
// ADD MEMBER MODAL
// ============================================
const AddMemberModal = ({ onClose, title = "Ajouter un membre", groupsOnly = false }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIds, setSelectedIds] = useState([]);

  const results = searchQuery.length >= 2
    ? mockSearchResults.filter(r =>
        (r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
         r.email.toLowerCase().includes(searchQuery.toLowerCase())) &&
        (!groupsOnly || r.type === 'Groupe')
      )
    : [];

  const toggleSelect = (id) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter(i => i !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <div style={styles.modalHeader}>
          <h3 style={styles.modalTitle}>{title}</h3>
          <button style={styles.modalClose} onClick={onClose}>✕</button>
        </div>
        <div style={styles.modalBody}>
          <div style={styles.searchInputModal}>
            <SearchIcon />
            <input
              type="text"
              placeholder={groupsOnly ? "Rechercher un groupe..." : "Rechercher un utilisateur ou un groupe..."}
              style={styles.searchInputModalField}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          
          {results.length > 0 && (
            <>
              <p style={styles.resultsLabel}>Résultats suggérés :</p>
              <div style={styles.searchResults}>
                {results.map(result => (
                  <div
                    key={result.id}
                    style={{
                      ...styles.resultItem,
                      ...(selectedIds.includes(result.id) ? styles.resultItemSelected : {})
                    }}
                    onClick={() => toggleSelect(result.id)}
                  >
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(result.id)}
                      onChange={() => {}}
                    />
                    <div style={styles.resultAvatar}>
                      {result.type === 'Groupe' ? '👥' : result.name.charAt(0)}
                    </div>
                    <div style={styles.resultInfoModal}>
                      <div style={styles.resultNameModal}>{result.name}</div>
                      <div style={styles.resultEmailModal}>{result.email}</div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
        <div style={styles.modalFooter}>
          <button style={{...styles.btn, ...styles.btnSecondary}} onClick={onClose}>
            Annuler
          </button>
          <button
            style={{...styles.btn, ...styles.btnPrimary, opacity: selectedIds.length === 0 ? 0.5 : 1}}
            disabled={selectedIds.length === 0}
            onClick={() => {
              alert(`Ajout de ${selectedIds.length} élément(s)`);
              onClose();
            }}
          >
            Ajouter la sélection
          </button>
        </div>
      </div>
    </div>
  );
};

// ============================================
// CONFIRM MODAL
// ============================================
const ConfirmModal = ({ title, message, onConfirm, onCancel, danger = false }) => (
  <div style={styles.modalOverlay} onClick={onCancel}>
    <div style={{...styles.modalContent, width: '450px'}} onClick={(e) => e.stopPropagation()}>
      <div style={styles.modalHeader}>
        <h3 style={styles.modalTitle}>{title}</h3>
        <button style={styles.modalClose} onClick={onCancel}>✕</button>
      </div>
      <div style={styles.modalBody}>
        {typeof message === 'string' ? <p>{message}</p> : message}
      </div>
      <div style={styles.modalFooter}>
        <button style={{...styles.btn, ...styles.btnSecondary}} onClick={onCancel}>
          Annuler
        </button>
        <button
          style={{...styles.btn, ...(danger ? styles.btnDangerSolid : styles.btnDangerSolid)}}
          onClick={onConfirm}
        >
          {danger ? 'Retirer' : 'Supprimer'}
        </button>
      </div>
    </div>
  </div>
);

// ============================================
// MAIN APP COMPONENT
// ============================================
export default function HestiaMailingLists() {
  const [view, setView] = useState('search');
  const [selectedML, setSelectedML] = useState(null);

  return (
    <div style={styles.appContainer}>
      <Header />
      <Navigation activeItem="mailing-lists" />
      
      <main style={styles.mainContent}>
        {view === 'search' && (
          <SearchPage onSelect={(ml) => {
            setSelectedML(ml);
            setView('detail');
          }} />
        )}
        {view === 'detail' && selectedML && (
          <DetailPage
            mailingList={selectedML}
            onBack={() => {
              setView('search');
              setSelectedML(null);
            }}
          />
        )}
      </main>
    </div>
  );
}

// ============================================
// STYLES
// ============================================
const styles = {
  appContainer: {
    minHeight: '100vh',
    background: '#F5F7FA',
    fontFamily: "'Segoe UI', Arial, sans-serif",
  },
  
  // Header
  header: {
    background: 'white',
    padding: '12px 32px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottom: '1px solid #E0E0E0',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.05)',
  },
  headerLogo: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  logoText: {
    fontSize: '28px',
    fontWeight: 700,
    color: '#2E7D32',
  },
  logoStar: {
    fontSize: '28px',
    color: '#FFD700',
  },
  headerUser: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  userName: {
    color: '#666',
    fontSize: '14px',
  },
  userAvatar: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    background: '#E0E0E0',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  langSelector: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    padding: '4px 8px',
    border: '1px solid #E0E0E0',
    borderRadius: '4px',
  },
  langCode: {
    fontSize: '12px',
  },

  // Navigation
  navigation: {
    background: 'white',
    padding: '16px 32px',
    display: 'flex',
    gap: '12px',
    borderBottom: '1px solid #E0E0E0',
  },
  navBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '10px 20px',
    border: '1px solid #E0E0E0',
    borderRadius: '25px',
    background: 'white',
    color: '#333',
    fontSize: '14px',
    fontWeight: 400,
    cursor: 'pointer',
  },
  navBtnActive: {
    border: '2px solid #4CAF50',
    background: '#E8F5E9',
    color: '#2E7D32',
    fontWeight: 600,
  },

  // Main content
  mainContent: {
    minHeight: 'calc(100vh - 130px)',
  },

  // Search page
  searchPage: {
    padding: '32px',
    maxWidth: '900px',
    margin: '0 auto',
  },
  pageTitle: {
    fontSize: '24px',
    fontWeight: 600,
    color: '#333',
    marginBottom: '24px',
  },
  searchBar: {
    display: 'flex',
    alignItems: 'center',
    background: 'white',
    borderRadius: '8px',
    padding: '12px 20px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
    marginBottom: '24px',
    gap: '12px',
  },
  searchInput: {
    flex: 1,
    border: 'none',
    outline: 'none',
    fontSize: '14px',
    color: '#333',
  },
  loader: {
    width: '20px',
    height: '20px',
    border: '2px solid #E0E0E0',
    borderTopColor: '#4CAF50',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  resultsContainer: {
    marginTop: '16px',
  },
  resultsCount: {
    color: '#666',
    fontSize: '14px',
    marginBottom: '12px',
  },
  resultsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  resultCard: {
    background: 'white',
    borderRadius: '8px',
    padding: '16px 20px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    cursor: 'pointer',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.05)',
    border: '1px solid #E0E0E0',
    transition: 'all 0.2s ease',
  },
  resultLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  resultIcon: {
    width: '44px',
    height: '44px',
    borderRadius: '50%',
    background: '#E3F2FD',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '20px',
  },
  resultInfo: {
    display: 'flex',
    flexDirection: 'column',
  },
  resultName: {
    fontWeight: 600,
    fontSize: '15px',
    color: '#333',
  },
  resultEmail: {
    color: '#666',
    fontSize: '13px',
  },
  resultRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  badgeMembers: {
    background: '#E8F5E9',
    color: '#2E7D32',
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: 500,
  },
  badgeType: {
    background: '#F5F5F5',
    color: '#666',
    fontSize: '11px',
    padding: '4px 10px',
    borderRadius: '4px',
  },
  emptyState: {
    textAlign: 'center',
    padding: '60px 20px',
    color: '#999',
  },
  emptyIcon: {
    fontSize: '48px',
    marginBottom: '16px',
  },

  // Detail page
  detailPage: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '32px',
  },
  detailHeader: {
    background: 'white',
    borderRadius: '8px',
    padding: '20px 24px',
    marginBottom: '24px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  btnBack: {
    background: 'none',
    border: '1px solid #E0E0E0',
    borderRadius: '8px',
    padding: '8px 12px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    color: '#666',
    fontSize: '13px',
  },
  mlIcon: {
    width: '48px',
    height: '48px',
    borderRadius: '50%',
    background: '#E3F2FD',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '24px',
  },
  mlInfo: {
    display: 'flex',
    flexDirection: 'column',
  },
  mlName: {
    margin: 0,
    fontSize: '20px',
    fontWeight: 600,
    color: '#333',
  },
  mlEmail: {
    margin: '4px 0 0',
    color: '#666',
    fontSize: '14px',
  },
  badgeMembersLg: {
    background: '#E8F5E9',
    color: '#2E7D32',
    padding: '6px 16px',
    borderRadius: '16px',
    fontSize: '13px',
    fontWeight: 500,
  },
  tabsBar: {
    background: 'white',
    borderRadius: '8px 8px 0 0',
    borderBottom: '1px solid #E0E0E0',
    display: 'flex',
  },
  tab: {
    padding: '12px 24px',
    border: 'none',
    borderBottom: '3px solid transparent',
    background: 'transparent',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 400,
    color: '#666',
  },
  tabActive: {
    borderBottomColor: '#4CAF50',
    color: '#4CAF50',
    fontWeight: 600,
  },
  tabContent: {
    background: 'white',
    borderRadius: '0 0 8px 8px',
    padding: '24px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
    minHeight: '400px',
  },

  // Properties form
  propertiesForm: {
    maxWidth: '800px',
  },
  formGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '20px',
    marginBottom: '24px',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
  },
  formLabel: {
    marginBottom: '6px',
    fontSize: '13px',
    fontWeight: 500,
    color: '#666',
  },
  formInput: {
    padding: '12px 16px',
    border: '1px solid #E0E0E0',
    borderRadius: '6px',
    fontSize: '14px',
    color: '#333',
    outline: 'none',
  },
  formInputReadonly: {
    background: '#F5F5F5',
    color: '#999',
    cursor: 'not-allowed',
  },
  formTextarea: {
    padding: '12px 16px',
    border: '1px solid #E0E0E0',
    borderRadius: '6px',
    fontSize: '14px',
    color: '#333',
    resize: 'vertical',
    minHeight: '80px',
    outline: 'none',
    fontFamily: 'inherit',
  },
  alertChanges: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    background: '#FFF8E1',
    border: '1px solid #FFE082',
    borderRadius: '6px',
    padding: '12px 16px',
    marginBottom: '20px',
    color: '#F57C00',
    fontSize: '13px',
  },
  formActions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '12px',
  },

  // Buttons
  btn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 16px',
    borderRadius: '6px',
    fontSize: '13px',
    fontWeight: 500,
    cursor: 'pointer',
    border: 'none',
  },
  btnPrimary: {
    background: '#4CAF50',
    color: 'white',
  },
  btnSecondary: {
    background: 'white',
    color: '#666',
    border: '1px solid #E0E0E0',
  },
  btnDanger: {
    background: 'white',
    color: '#EF5350',
    border: '1px solid #EF5350',
  },
  btnDangerSolid: {
    background: '#EF5350',
    color: 'white',
  },
  btnOutlineDanger: {
    background: 'white',
    color: '#EF5350',
    border: '1px solid #EF5350',
  },
  btnIcon: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '16px',
    padding: '4px',
  },

  // Table
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    padding: '12px 16px',
    textAlign: 'left',
    background: '#F5F5F5',
    fontSize: '12px',
    fontWeight: 600,
    color: '#666',
  },
  td: {
    padding: '12px 16px',
    fontSize: '14px',
    borderBottom: '1px solid #E0E0E0',
  },

  // Actions bar
  actionsBar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
  },
  actionsLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  actionsRight: {
    display: 'flex',
    gap: '12px',
  },
  filterInput: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    background: '#F5F5F5',
    borderRadius: '6px',
    padding: '8px 12px',
  },
  filterInputField: {
    border: 'none',
    background: 'transparent',
    outline: 'none',
    fontSize: '13px',
    width: '180px',
  },
  membersCount: {
    color: '#666',
    fontSize: '13px',
  },

  // Badges
  badgeUser: {
    display: 'inline-block',
    padding: '4px 8px',
    borderRadius: '4px',
    fontSize: '11px',
    background: '#F5F5F5',
    color: '#666',
  },
  badgeGroup: {
    display: 'inline-block',
    padding: '4px 8px',
    borderRadius: '4px',
    fontSize: '11px',
    background: '#E3F2FD',
    color: '#1976D2',
  },
  badgeInherited: {
    display: 'inline-block',
    padding: '4px 8px',
    borderRadius: '4px',
    fontSize: '11px',
    background: '#FFF3E0',
    color: '#E65100',
    marginLeft: '6px',
  },

  // Alerts
  alertInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    background: '#E3F2FD',
    borderRadius: '6px',
    padding: '12px 16px',
    marginBottom: '20px',
    color: '#1976D2',
    fontSize: '13px',
  },
  alertWarning: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
    background: '#FFF3E0',
    borderRadius: '6px',
    padding: '12px 16px',
    marginBottom: '20px',
    color: '#E65100',
    fontSize: '13px',
  },

  // Owners list
  ownersList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  ownerCard: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px',
    background: '#FAFAFA',
    borderRadius: '6px',
    border: '1px solid #E0E0E0',
  },
  ownerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  ownerAvatar: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    background: '#4CAF50',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 600,
    fontSize: '14px',
  },
  ownerInfo: {
    display: 'flex',
    flexDirection: 'column',
  },
  ownerName: {
    fontWeight: 500,
    fontSize: '14px',
  },
  ownerEmail: {
    color: '#666',
    fontSize: '13px',
  },

  // Modal
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  modalContent: {
    background: 'white',
    borderRadius: '12px',
    width: '500px',
    maxHeight: '80vh',
    overflow: 'hidden',
    boxShadow: '0 20px 40px rgba(0, 0, 0, 0.2)',
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px 24px',
    borderBottom: '1px solid #E0E0E0',
  },
  modalTitle: {
    margin: 0,
    fontSize: '18px',
    fontWeight: 600,
  },
  modalClose: {
    background: 'none',
    border: 'none',
    fontSize: '20px',
    color: '#999',
    cursor: 'pointer',
  },
  modalBody: {
    padding: '24px',
    maxHeight: '400px',
    overflowY: 'auto',
  },
  modalFooter: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '12px',
    padding: '16px 24px',
    borderTop: '1px solid #E0E0E0',
  },
  searchInputModal: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    background: '#F5F5F5',
    borderRadius: '6px',
    padding: '12px 16px',
    marginBottom: '20px',
  },
  searchInputModalField: {
    flex: 1,
    border: 'none',
    background: 'transparent',
    outline: 'none',
    fontSize: '14px',
  },
  resultsLabel: {
    color: '#666',
    fontSize: '13px',
    marginBottom: '12px',
  },
  searchResults: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  resultItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px',
    border: '1px solid #E0E0E0',
    borderRadius: '6px',
    cursor: 'pointer',
  },
  resultItemSelected: {
    borderColor: '#4CAF50',
    background: '#E8F5E9',
  },
  resultAvatar: {
    width: '36px',
    height: '36px',
    borderRadius: '50%',
    background: '#E0E0E0',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '14px',
  },
  resultInfoModal: {
    flex: 1,
  },
  resultNameModal: {
    fontSize: '14px',
    fontWeight: 500,
  },
  resultEmailModal: {
    fontSize: '12px',
    color: '#666',
  },
};

// Add CSS animation for loader
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;
document.head.appendChild(styleSheet);
