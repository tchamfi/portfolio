import React from 'react';

export default function HestiaArchitecture() {
  return (
    <div className="min-h-screen bg-slate-900 p-8 flex flex-col items-center justify-center">
      <h1 className="text-3xl font-bold text-white mb-2">Architecture Technique Hestia</h1>
      <p className="text-slate-400 mb-8">Flux d'intégration avec Azure Active Directory</p>
      
      <div className="flex items-center gap-4">
        {/* Utilisateur */}
        <div className="flex flex-col items-center">
          <div className="w-20 h-20 bg-gradient-to-br from-amber-400 to-amber-600 rounded-full flex items-center justify-center shadow-lg shadow-amber-500/30">
            <svg className="w-10 h-10 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>
          </div>
          <span className="mt-2 text-white font-semibold">Utilisateur</span>
          <span className="text-slate-400 text-sm">RH / IT / Admin</span>
        </div>

        {/* Flèche 1 */}
        <div className="flex flex-col items-center">
          <div className="w-16 h-1 bg-gradient-to-r from-amber-400 to-blue-400 rounded"></div>
          <span className="text-slate-500 text-xs mt-1">HTTPS</span>
        </div>

        {/* Frontend Hestia */}
        <div className="flex flex-col items-center">
          <div className="w-32 h-24 bg-gradient-to-br from-blue-500 to-blue-700 rounded-xl flex flex-col items-center justify-center shadow-lg shadow-blue-500/30 border border-blue-400/30">
            <svg className="w-8 h-8 text-white mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <span className="text-white font-bold text-sm">Hestia</span>
            <span className="text-blue-200 text-xs">Frontend</span>
          </div>
          <span className="mt-2 text-slate-400 text-xs">Interface Web</span>
        </div>

        {/* Flèche 2 */}
        <div className="flex flex-col items-center">
          <div className="w-16 h-1 bg-gradient-to-r from-blue-400 to-indigo-400 rounded"></div>
          <span className="text-slate-500 text-xs mt-1">REST API</span>
        </div>

        {/* Backend Hestia */}
        <div className="flex flex-col items-center">
          <div className="w-32 h-24 bg-gradient-to-br from-indigo-500 to-indigo-700 rounded-xl flex flex-col items-center justify-center shadow-lg shadow-indigo-500/30 border border-indigo-400/30">
            <svg className="w-8 h-8 text-white mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
            </svg>
            <span className="text-white font-bold text-sm">Hestia</span>
            <span className="text-indigo-200 text-xs">Back-end</span>
          </div>
          <span className="mt-2 text-slate-400 text-xs">Logique métier</span>
        </div>

        {/* Flèche 3 */}
        <div className="flex flex-col items-center">
          <div className="w-16 h-1 bg-gradient-to-r from-indigo-400 to-purple-400 rounded"></div>
          <span className="text-slate-500 text-xs mt-1">REST API</span>
        </div>

        {/* API User */}
        <div className="flex flex-col items-center">
          <div className="w-32 h-24 bg-gradient-to-br from-purple-500 to-purple-700 rounded-xl flex flex-col items-center justify-center shadow-lg shadow-purple-500/30 border border-purple-400/30">
            <svg className="w-8 h-8 text-white mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span className="text-white font-bold text-sm">API User</span>
            <span className="text-purple-200 text-xs">Middleware</span>
          </div>
          <span className="mt-2 text-slate-400 text-xs">Encapsulation</span>
        </div>

        {/* Flèche 4 - OAuth */}
        <div className="flex flex-col items-center">
          <div className="w-16 h-1 bg-gradient-to-r from-purple-400 to-cyan-400 rounded"></div>
          <span className="text-cyan-400 text-xs mt-1 font-semibold">OAuth 2.0</span>
        </div>

        {/* Microsoft Graph */}
        <div className="flex flex-col items-center">
          <div className="w-32 h-24 bg-gradient-to-br from-cyan-500 to-cyan-700 rounded-xl flex flex-col items-center justify-center shadow-lg shadow-cyan-500/30 border border-cyan-400/30">
            <svg className="w-8 h-8 text-white mb-1" fill="currentColor" viewBox="0 0 24 24">
              <path d="M11.5 3v8.5H3V3h8.5zm0 18H3v-8.5h8.5V21zm1-18H21v8.5h-8.5V3zm8.5 9.5V21h-8.5v-8.5H21z"/>
            </svg>
            <span className="text-white font-bold text-sm">MS Graph</span>
            <span className="text-cyan-200 text-xs">API</span>
          </div>
          <span className="mt-2 text-slate-400 text-xs">Microsoft</span>
        </div>

        {/* Flèche 5 */}
        <div className="flex flex-col items-center">
          <div className="w-16 h-1 bg-gradient-to-r from-cyan-400 to-sky-400 rounded"></div>
          <span className="text-slate-500 text-xs mt-1">Graph</span>
        </div>

        {/* Azure AD */}
        <div className="flex flex-col items-center">
          <div className="w-32 h-24 bg-gradient-to-br from-sky-500 to-sky-700 rounded-xl flex flex-col items-center justify-center shadow-lg shadow-sky-500/30 border border-sky-400/30">
            <svg className="w-8 h-8 text-white mb-1" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
            <span className="text-white font-bold text-sm">Azure AD</span>
            <span className="text-sky-200 text-xs">Annuaire</span>
          </div>
          <span className="mt-2 text-slate-400 text-xs">Identités</span>
        </div>
      </div>

      {/* Légende des opérations */}
      <div className="mt-12 bg-slate-800/50 rounded-xl p-6 border border-slate-700 max-w-4xl">
        <h2 className="text-white font-semibold mb-4 text-center">Opérations via Azure AD</h2>
        <div className="grid grid-cols-4 gap-4">
          <div className="flex items-center gap-2 bg-slate-700/50 rounded-lg p-3">
            <div className="w-8 h-8 bg-green-500/20 rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
            </div>
            <div>
              <p className="text-white text-sm font-medium">Création</p>
              <p className="text-slate-400 text-xs">Comptes utilisateurs</p>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-slate-700/50 rounded-lg p-3">
            <div className="w-8 h-8 bg-amber-500/20 rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
              </svg>
            </div>
            <div>
              <p className="text-white text-sm font-medium">Licences</p>
              <p className="text-slate-400 text-xs">Attribution M365</p>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-slate-700/50 rounded-lg p-3">
            <div className="w-8 h-8 bg-blue-500/20 rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div>
              <p className="text-white text-sm font-medium">Groupes</p>
              <p className="text-slate-400 text-xs">Mailing Lists</p>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-slate-700/50 rounded-lg p-3">
            <div className="w-8 h-8 bg-red-500/20 rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
              </svg>
            </div>
            <div>
              <p className="text-white text-sm font-medium">Désactivation</p>
              <p className="text-slate-400 text-xs">Offboarding</p>
            </div>
          </div>
        </div>
      </div>

      {/* Sécurité */}
      <div className="mt-6 flex items-center gap-2 text-slate-400">
        <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        <span className="text-sm">Authentification OAuth 2.0 via Application Service avec jeton sécurisé</span>
      </div>
    </div>
  );
}
