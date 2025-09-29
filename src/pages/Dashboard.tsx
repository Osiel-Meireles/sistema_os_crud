import React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

// Mock data - será substituído por dados reais da API
const mockStats = {
  totalOS: 156,
  emAberto: 23,
  finalizadas: 98,
  aguardandoPecas: 12,
}

const mockTecnicos = [
  { nome: 'ABIMADÉSIO', quantidade: 25 },
  { nome: 'ANTONY CAUÃ', quantidade: 18 },
  { nome: 'DIEGO CARDOSO', quantidade: 22 },
  { nome: 'DIEL BATISTA', quantidade: 15 },
  { nome: 'JOSAFÁ MEDEIROS', quantidade: 20 },
  { nome: 'MAYKON RODOLFO', quantidade: 16 },
  { nome: 'ROMÉRIO CIRQUEIRA', quantidade: 19 },
  { nome: 'VALMIR FRANCISCO', quantidade: 21 },
]

const mockSecretarias = [
  { nome: 'FAZENDA', quantidade: 45 },
  { nome: 'EDUCAÇÃO', quantidade: 32 },
  { nome: 'SAÚDE', quantidade: 28 },
  { nome: 'INFRAESTRUTURA', quantidade: 25 },
  { nome: 'GOVERNO', quantidade: 15 },
  { nome: 'OUTROS', quantidade: 11 },
]

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

export default function Dashboard() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard de Indicadores</h1>
        <p className="text-gray-600">Visão geral das ordens de serviço do ano corrente</p>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <div className="card-content">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total de OS</p>
                <p className="text-3xl font-bold text-blue-600">{mockStats.totalOS}</p>
              </div>
              <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <div className="h-6 w-6 bg-blue-600 rounded"></div>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-content">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Em Aberto</p>
                <p className="text-3xl font-bold text-yellow-600">{mockStats.emAberto}</p>
              </div>
              <div className="h-12 w-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                <div className="h-6 w-6 bg-yellow-600 rounded"></div>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-content">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Finalizadas</p>
                <p className="text-3xl font-bold text-green-600">{mockStats.finalizadas}</p>
              </div>
              <div className="h-12 w-12 bg-green-100 rounded-lg flex items-center justify-center">
                <div className="h-6 w-6 bg-green-600 rounded"></div>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-content">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Aguardando Peças</p>
                <p className="text-3xl font-bold text-orange-600">{mockStats.aguardandoPecas}</p>
              </div>
              <div className="h-12 w-12 bg-orange-100 rounded-lg flex items-center justify-center">
                <div className="h-6 w-6 bg-orange-600 rounded"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Técnicos chart */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">OS por Técnico</h3>
          </div>
          <div className="card-content">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={mockTecnicos}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="nome" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  fontSize={12}
                />
                <YAxis />
                <Tooltip />
                <Bar dataKey="quantidade" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Secretarias chart */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">OS por Secretaria</h3>
          </div>
          <div className="card-content">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={mockSecretarias}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ nome, percent }) => `${nome} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="quantidade"
                >
                  {mockSecretarias.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Técnicos table */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Ranking de Técnicos</h3>
          </div>
          <div className="card-content">
            <div className="overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Técnico
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quantidade
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {mockTecnicos
                    .sort((a, b) => b.quantidade - a.quantidade)
                    .map((tecnico, index) => (
                    <tr key={tecnico.nome}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {tecnico.nome}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {tecnico.quantidade}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Secretarias table */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">OS por Secretaria</h3>
          </div>
          <div className="card-content">
            <div className="overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Secretaria
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quantidade
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {mockSecretarias
                    .sort((a, b) => b.quantidade - a.quantidade)
                    .map((secretaria) => (
                    <tr key={secretaria.nome}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {secretaria.nome}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {secretaria.quantidade}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}