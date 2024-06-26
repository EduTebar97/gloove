// src/routes.tsx
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import Home from "./components/Pages/Home";

import PropietariosLayout from './components/Propietarios/PropietariosValidados/PropietariosLayout';
import PropietariosDashboard from './components/Propietarios/PropietariosValidados/Dashboard';
import PropertyForm from './components/Propietarios/PropietariosValidados/PropertyForm';
import Properties from './components/Propietarios/PropietariosValidados/Properties';
import Chat from './components/Propietarios/PropietariosValidados/Chat';

import ProcesoDeAlta from './components/Propietarios/ProcesoDeAlta/ProcesoDeAlta';

import HuespedesLayout from './components/Huespedes/HuespedesLayout';
import HuespedesDashboard from './components/Huespedes/Dashboard';

import EmpleadosLayout from './components/Empleados/EmpleadosLayout';
import EmpleadosDashboard from './components/Empleados/Dashboard';

const AppRoutes: React.FC = () => {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/" element={<Home />} />

      {user && user.role === 'propietario' && (
        <>
          <Route element={<PropietariosLayout />}>
            <Route path="/dashboard-propietarios" element={<PropietariosDashboard />} />
            <Route path="/property-form" element={<PropertyForm />} />
            <Route path="/properties" element={<Properties />} />
            <Route path="/chat" element={<Chat />} />
          </Route>
          <Route path="/proceso-de-alta" element={<ProcesoDeAlta />} />
        </>
      )}

      {user && user.role === 'huesped' && (
        <Route element={<HuespedesLayout />}>
          <Route path="/dashboard-huespedes" element={<HuespedesDashboard />} />
        </Route>
      )}

      {user && user.role === 'empleado' && (
        <Route element={<EmpleadosLayout />}>
          <Route path="/dashboard-empleados" element={<EmpleadosDashboard />} />
          {/* Agrega las demás rutas de empleados aquí */}
        </Route>
      )}

      {!user && <Route path="*" element={<Login />} />}
    </Routes>
  );
};

export default AppRoutes;

