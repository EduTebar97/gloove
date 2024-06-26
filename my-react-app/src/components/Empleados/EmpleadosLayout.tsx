import React, { ReactNode } from 'react';
import { Link } from 'react-router-dom';

interface EmpleadosLayoutProps {
  children: ReactNode;
}

const EmpleadosLayout: React.FC<EmpleadosLayoutProps> = ({ children }) => {
  return (
    <div className="flex h-screen bg-gray-100">
      <aside className="w-56 bg-white border-r border-gray-200 p-4">
        <div className="mb-8">
          <div className="bg-gray-300 h-12 mb-4"></div> {/* Placeholder for Logo */}
          <nav>
            <ul className="space-y-4">
              <li><Link to="/dashboard" className="text-blue-600 font-bold">Dashboard</Link></li>
              <li><Link to="/owners" className="text-gray-600">Propietarios</Link></li>
              <li><Link to="/guests" className="text-gray-600">Huéspedes</Link></li>
              <li><Link to="/notifications" className="text-gray-600">Notificaciones</Link></li>
              <li><Link to="/profile" className="text-gray-600">Mi Perfil</Link></li>
              <li><Link to="/settings" className="text-gray-600">Configuraciones</Link></li>
              <li><Link to="/help" className="text-gray-600">Help</Link></li>
            </ul>
          </nav>
        </div>
      </aside>
      <div className="flex-1">
        <header className="bg-white shadow p-4 flex items-center justify-between">
          <div className="flex items-center">
            <div className="bg-gray-300 w-10 h-10 rounded-full mr-4"></div> {/* Placeholder for User Photo */}
            <div>
              <div className="text-blue-600 font-bold">Empleado</div>
              <div className="text-gray-600">Hola XXXXX</div>
            </div>
          </div>
          <button className="bg-blue-500 text-white px-4 py-2 rounded-full flex items-center">
            <span className="mr-2">Pregúntanos</span>
            <div className="bg-white w-4 h-4 rounded-full flex items-center justify-center transform rotate-45">
              <div className="bg-blue-500 w-2 h-2"></div>
            </div>
          </button>
        </header>
        <main className="p-8">
          {children}
        </main>
      </div>
    </div>
  );
};

export default EmpleadosLayout;

