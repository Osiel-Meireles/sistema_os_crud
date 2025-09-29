import React from 'react'
import { Link } from 'react-router-dom'
import { FileText, ExternalLink, Search, Edit, BarChart3 } from 'lucide-react'

const quickActions = [
  {
    name: 'OS Internas',
    description: 'Registrar nova ordem de serviço interna',
    href: '/os-interna',
    icon: FileText,
    color: 'bg-blue-500',
  },
  {
    name: 'OS Externas',
    description: 'Registrar nova ordem de serviço externa',
    href: '/os-externa',
    icon: ExternalLink,
    color: 'bg-green-500',
  },
  {
    name: 'Filtrar OS',
    description: 'Buscar e filtrar ordens de serviço',
    href: '/filtrar',
    icon: Search,
    color: 'bg-purple-500',
  },
  {
    name: 'Atualizar OS',
    description: 'Atualizar status e dar baixa em OS',
    href: '/atualizar',
    icon: Edit,
    color: 'bg-orange-500',
  },
]

export default function Home() {
  return (
    <div className="space-y-8">
      {/* Welcome section */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
          Bem-vindo ao Sistema de OS
        </h1>
        <p className="mt-4 text-lg text-gray-600">
          Gerencie suas ordens de serviço de forma eficiente e organizada
        </p>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {quickActions.map((action) => (
          <Link
            key={action.name}
            to={action.href}
            className="group relative overflow-hidden rounded-lg bg-white p-6 shadow-sm ring-1 ring-gray-200 transition-all hover:shadow-md hover:ring-gray-300"
          >
            <div className="flex items-center space-x-3">
              <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${action.color}`}>
                <action.icon className="h-6 w-6 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-medium text-gray-900 group-hover:text-primary-600">
                  {action.name}
                </h3>
                <p className="text-sm text-gray-500 mt-1">
                  {action.description}
                </p>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Dashboard preview */}
      <div className="card">
        <div className="card-header">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">
              Visão Geral Rápida
            </h2>
            <Link
              to="/dashboard"
              className="btn btn-outline text-sm"
            >
              <BarChart3 className="h-4 w-4 mr-2" />
              Ver Dashboard Completo
            </Link>
          </div>
        </div>
        <div className="card-content">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">--</div>
              <div className="text-sm text-blue-800">Total de OS</div>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">--</div>
              <div className="text-sm text-yellow-800">Em Aberto</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">--</div>
              <div className="text-sm text-green-800">Finalizadas</div>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">--</div>
              <div className="text-sm text-orange-800">Aguardando Peças</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}