import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Search, Download, Eye, X } from 'lucide-react'

interface FiltroForm {
  tipo_os: string
  status: string
  secretaria: string
  tecnico: string
  categoria: string
  equipamento: string
  data_inicio: string
  data_fim: string
  numero_os: string
  patrimonio: string
}

const statusOptions = [
  'Todos', 'EM ABERTO', 'AGUARDANDO PEÇA(S)', 'FINALIZADO', 'AGUARDANDO RETIRADA', 'ENTREGUE AO CLIENTE'
]

const secretarias = [
  'Todas', 'CIDADANIA', 'CONTROLE INTERNO', 'CULTURA E ESPORTES', 'DESENVOLVIMENTO ECONÔMICO',
  'EDUCAÇÃO', 'FAZENDA', 'FORÇA POLICIAL', 'GOVERNO', 'INFRAESTRUTURA', 'OUTROS',
  'PROCURADORIA', 'SAÚDE', 'SEGURANÇA', 'SUSTENTABILIDADE'
]

const tecnicos = [
  'Todos', 'ABIMADÉSIO', 'ANTONY CAUÃ', 'DIEGO CARDOSO', 'DIEL BATISTA',
  'JOSAFÁ MEDEIROS', 'MAYKON RODOLFO', 'ROMÉRIO CIRQUEIRA', 'VALMIR FRANCISCO'
]

// Mock data para demonstração
const mockResults = [
  {
    id: 1,
    numero: '1-25',
    tipo: 'Interna',
    status: 'EM ABERTO',
    secretaria: 'FAZENDA',
    solicitante: 'João Silva',
    data: '2025-01-15',
    data_finalizada: null,
  },
  {
    id: 2,
    numero: '2-25',
    tipo: 'Externa',
    status: 'FINALIZADO',
    secretaria: 'EDUCAÇÃO',
    solicitante: 'Maria Santos',
    data: '2025-01-14',
    data_finalizada: '2025-01-16 14:30:00',
  },
]

export default function FiltrarOS() {
  const [isSearching, setIsSearching] = useState(false)
  const [results, setResults] = useState<any[]>([])
  const [selectedOS, setSelectedOS] = useState<any>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 10

  const { register, handleSubmit, reset } = useForm<FiltroForm>()

  const onSubmit = async (data: FiltroForm) => {
    setIsSearching(true)
    try {
      // Aqui será feita a chamada para a API
      console.log('Filtros aplicados:', data)
      
      // Simular delay da API
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Usar dados mock por enquanto
      setResults(mockResults)
      setCurrentPage(1)
    } catch (error) {
      alert('Erro ao buscar ordens de serviço')
    } finally {
      setIsSearching(false)
    }
  }

  const handleExport = () => {
    // Implementar exportação
    alert('Funcionalidade de exportação será implementada')
  }

  const handleViewDetails = (os: any) => {
    setSelectedOS(os)
  }

  const totalPages = Math.ceil(results.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const currentResults = results.slice(startIndex, endIndex)

  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3">
        <Search className="h-8 w-8 text-purple-600" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Filtrar Ordens de Serviço</h1>
          <p className="text-gray-600">Busque e filtre ordens de serviço por diversos critérios</p>
        </div>
      </div>

      {/* Filtros */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold text-gray-900">Filtros de Busca</h2>
        </div>
        <div className="card-content">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tipo de OS
                </label>
                <select {...register('tipo_os')} className="input">
                  <option value="Ambas">Ambas</option>
                  <option value="OS Interna">OS Interna</option>
                  <option value="OS Externa">OS Externa</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status
                </label>
                <select {...register('status')} className="input">
                  {statusOptions.map(status => (
                    <option key={status} value={status}>{status}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Secretaria
                </label>
                <select {...register('secretaria')} className="input">
                  {secretarias.map(secretaria => (
                    <option key={secretaria} value={secretaria}>{secretaria}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Data de Início
                </label>
                <input
                  type="date"
                  {...register('data_inicio')}
                  className="input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Data de Fim
                </label>
                <input
                  type="date"
                  {...register('data_fim')}
                  className="input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Número da OS
                </label>
                <input
                  type="text"
                  {...register('numero_os')}
                  className="input"
                  placeholder="Ex: 1-25"
                />
              </div>
            </div>

            <details className="group">
              <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                Mais Filtros...
              </summary>
              <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Técnico
                  </label>
                  <select {...register('tecnico')} className="input">
                    {tecnicos.map(tecnico => (
                      <option key={tecnico} value={tecnico}>{tecnico}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Categoria
                  </label>
                  <select {...register('categoria')} className="input">
                    <option value="Todas">Todas</option>
                    <option value="COMPUTADORES">COMPUTADORES</option>
                    <option value="IMPRESSORAS">IMPRESSORAS</option>
                    <option value="REDES">REDES</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Patrimônio
                  </label>
                  <input
                    type="text"
                    {...register('patrimonio')}
                    className="input"
                    placeholder="Número do patrimônio"
                  />
                </div>
              </div>
            </details>

            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => reset()}
                className="btn btn-outline"
                disabled={isSearching}
              >
                Limpar
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isSearching}
              >
                {isSearching ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Buscando...
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4 mr-2" />
                    Filtrar
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Resultados */}
      {results.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                Resultados da Busca ({results.length} encontrados)
              </h2>
              <div className="flex space-x-2">
                <button
                  onClick={handleExport}
                  className="btn btn-outline text-sm"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Exportar
                </button>
                <button
                  onClick={() => setResults([])}
                  className="btn btn-outline text-sm"
                >
                  Limpar Resultados
                </button>
              </div>
            </div>
          </div>
          <div className="card-content">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Ação
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Número
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Secretaria
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Solicitante
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Data
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {currentResults.map((os) => (
                    <tr key={os.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => handleViewDetails(os)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {os.numero}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {os.tipo}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          os.status === 'EM ABERTO' ? 'bg-yellow-100 text-yellow-800' :
                          os.status === 'FINALIZADO' ? 'bg-green-100 text-green-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {os.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {os.secretaria}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {os.solicitante}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(os.data).toLocaleDateString('pt-BR')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Paginação */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-6">
                <div className="text-sm text-gray-700">
                  Mostrando {startIndex + 1} a {Math.min(endIndex, results.length)} de {results.length} resultados
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                    disabled={currentPage === 1}
                    className="btn btn-outline text-sm"
                  >
                    Anterior
                  </button>
                  <span className="px-3 py-2 text-sm text-gray-700">
                    Página {currentPage} de {totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                    disabled={currentPage === totalPages}
                    className="btn btn-outline text-sm"
                  >
                    Próxima
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modal de detalhes */}
      {selectedOS && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setSelectedOS(null)}></div>
            
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    Detalhes da OS {selectedOS.numero}
                  </h3>
                  <button
                    onClick={() => setSelectedOS(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="h-6 w-6" />
                  </button>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <span className="font-medium text-gray-700">Tipo:</span> {selectedOS.tipo}
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Status:</span> {selectedOS.status}
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Secretaria:</span> {selectedOS.secretaria}
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Solicitante:</span> {selectedOS.solicitante}
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Data:</span> {new Date(selectedOS.data).toLocaleDateString('pt-BR')}
                  </div>
                  {selectedOS.data_finalizada && (
                    <div>
                      <span className="font-medium text-gray-700">Data de Finalização:</span> {selectedOS.data_finalizada}
                    </div>
                  )}
                </div>
              </div>
              
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  onClick={() => setSelectedOS(null)}
                  className="btn btn-outline w-full sm:w-auto"
                >
                  Fechar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}