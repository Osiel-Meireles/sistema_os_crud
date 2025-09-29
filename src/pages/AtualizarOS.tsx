import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Edit, Search, Save, FileText } from 'lucide-react'

interface BuscaForm {
  tipo_os: string
  numero_os: string
}

interface AtualizacaoForm {
  status: string
  servico_executado: string
  retirada_por: string
}

const statusOptions = [
  'EM ABERTO', 'AGUARDANDO PEÇA(S)', 'FINALIZADO', 'AGUARDANDO RETIRADA', 'ENTREGUE AO CLIENTE'
]

// Mock data para demonstração
const mockOS = {
  numero: '1-25',
  tipo: 'Interna',
  secretaria: 'FAZENDA',
  setor: 'TI',
  solicitante: 'João Silva',
  telefone: '(11) 99999-9999',
  data: '2025-01-15',
  hora: '14:30:00',
  tecnico: 'DIEGO CARDOSO',
  equipamento: 'COMPUTADOR',
  categoria: 'COMPUTADORES',
  patrimonio: '12345',
  status: 'EM ABERTO',
  solicitacao_cliente: 'Computador não liga, tela azul da morte.',
  servico_executado: '',
  retirada_por: '',
}

export default function AtualizarOS() {
  const [osEncontrada, setOSEncontrada] = useState<any>(null)
  const [isBuscando, setIsBuscando] = useState(false)
  const [isAtualizando, setIsAtualizando] = useState(false)

  const { register: registerBusca, handleSubmit: handleSubmitBusca } = useForm<BuscaForm>()
  const { register: registerAtualizacao, handleSubmit: handleSubmitAtualizacao, watch } = useForm<AtualizacaoForm>()

  const statusAtual = watch('status')

  const onBuscar = async (data: BuscaForm) => {
    setIsBuscando(true)
    try {
      // Aqui será feita a chamada para a API
      console.log('Buscando OS:', data)
      
      // Simular delay da API
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Usar dados mock por enquanto
      if (data.numero_os === '1-25') {
        setOSEncontrada(mockOS)
      } else {
        setOSEncontrada(null)
        alert('OS não encontrada')
      }
    } catch (error) {
      alert('Erro ao buscar OS')
    } finally {
      setIsBuscando(false)
    }
  }

  const onAtualizar = async (data: AtualizacaoForm) => {
    setIsAtualizando(true)
    try {
      // Aqui será feita a chamada para a API
      console.log('Atualizando OS:', data)
      
      // Simular delay da API
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      alert('OS atualizada com sucesso!')
      
      // Atualizar os dados locais
      if (osEncontrada) {
        setOSEncontrada({
          ...osEncontrada,
          ...data,
          status: data.status === 'FINALIZADO' ? 'AGUARDANDO RETIRADA' : data.status
        })
      }
    } catch (error) {
      alert('Erro ao atualizar OS')
    } finally {
      setIsAtualizando(false)
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3">
        <Edit className="h-8 w-8 text-orange-600" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Atualizar Ordem de Serviço</h1>
          <p className="text-gray-600">Busque uma OS para atualizar seu status ou dar baixa</p>
        </div>
      </div>

      {/* Busca de OS */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold text-gray-900">Buscar OS</h2>
        </div>
        <div className="card-content">
          <form onSubmit={handleSubmitBusca(onBuscar)} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tipo de OS
                </label>
                <select {...registerBusca('tipo_os')} className="input">
                  <option value="OS Interna">OS Interna</option>
                  <option value="OS Externa">OS Externa</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Número da OS *
                </label>
                <input
                  type="text"
                  {...registerBusca('numero_os', { required: true })}
                  className="input"
                  placeholder="Ex: 1-25"
                />
              </div>
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isBuscando}
              >
                {isBuscando ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Buscando...
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4 mr-2" />
                    Buscar OS
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Informações da OS encontrada */}
      {osEncontrada && (
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-gray-900">
              Informações da OS {osEncontrada.numero}
            </h2>
          </div>
          <div className="card-content">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              <div>
                <span className="text-sm font-medium text-gray-500">Tipo:</span>
                <p className="text-sm text-gray-900">{osEncontrada.tipo}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">Status:</span>
                <p className="text-sm text-gray-900">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    osEncontrada.status === 'EM ABERTO' ? 'bg-yellow-100 text-yellow-800' :
                    osEncontrada.status === 'FINALIZADO' ? 'bg-green-100 text-green-800' :
                    osEncontrada.status === 'AGUARDANDO RETIRADA' ? 'bg-blue-100 text-blue-800' :
                    osEncontrada.status === 'ENTREGUE AO CLIENTE' ? 'bg-green-100 text-green-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {osEncontrada.status}
                  </span>
                </p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">Secretaria:</span>
                <p className="text-sm text-gray-900">{osEncontrada.secretaria}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">Setor:</span>
                <p className="text-sm text-gray-900">{osEncontrada.setor}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">Solicitante:</span>
                <p className="text-sm text-gray-900">{osEncontrada.solicitante}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">Telefone:</span>
                <p className="text-sm text-gray-900">{osEncontrada.telefone}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">Data:</span>
                <p className="text-sm text-gray-900">{new Date(osEncontrada.data).toLocaleDateString('pt-BR')}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">Técnico:</span>
                <p className="text-sm text-gray-900">{osEncontrada.tecnico}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">Equipamento:</span>
                <p className="text-sm text-gray-900">{osEncontrada.equipamento}</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <span className="text-sm font-medium text-gray-500">Solicitação do Cliente:</span>
                <p className="text-sm text-gray-900 mt-1 p-3 bg-gray-50 rounded-md">
                  {osEncontrada.solicitacao_cliente}
                </p>
              </div>
              
              {osEncontrada.servico_executado && (
                <div>
                  <span className="text-sm font-medium text-gray-500">Serviço Executado:</span>
                  <p className="text-sm text-gray-900 mt-1 p-3 bg-gray-50 rounded-md">
                    {osEncontrada.servico_executado}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Formulário de atualização */}
      {osEncontrada && osEncontrada.status !== 'ENTREGUE AO CLIENTE' && (
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-gray-900">Atualizar Status da OS</h2>
          </div>
          <div className="card-content">
            <form onSubmit={handleSubmitAtualizacao(onAtualizar)} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Novo Status *
                </label>
                <select
                  {...registerAtualizacao('status', { required: true })}
                  className="input"
                  defaultValue={osEncontrada.status}
                >
                  {statusOptions
                    .filter(status => status !== 'AGUARDANDO RETIRADA' && status !== 'ENTREGUE AO CLIENTE')
                    .map(status => (
                    <option key={status} value={status}>{status}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {statusAtual === 'FINALIZADO' ? 'Serviço Executado *' : 'Descrição da Atualização'}
                </label>
                <textarea
                  {...registerAtualizacao('servico_executado', { 
                    required: statusAtual === 'FINALIZADO' 
                  })}
                  rows={4}
                  className="input min-h-[100px] resize-y"
                  placeholder={statusAtual === 'FINALIZADO' ? 
                    'Descreva o serviço executado...' : 
                    'Descreva a atualização realizada...'
                  }
                  defaultValue={osEncontrada.servico_executado}
                />
              </div>

              <div className="flex justify-end space-x-4">
                <button
                  type="button"
                  onClick={() => setOSEncontrada(null)}
                  className="btn btn-outline"
                  disabled={isAtualizando}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isAtualizando}
                >
                  {isAtualizando ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Salvando...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      Salvar Alterações
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Registrar entrega */}
      {osEncontrada && (osEncontrada.status === 'AGUARDANDO RETIRADA' || osEncontrada.status === 'ENTREGUE AO CLIENTE') && (
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-gray-900">
              {osEncontrada.status === 'ENTREGUE AO CLIENTE' ? 'Informações da Entrega' : 'Registrar Entrega ao Cliente'}
            </h2>
          </div>
          <div className="card-content">
            {osEncontrada.status === 'ENTREGUE AO CLIENTE' ? (
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="text-green-800">
                  <strong>Esta OS já foi finalizada e entregue ao cliente.</strong>
                </p>
                {osEncontrada.retirada_por && (
                  <p className="text-green-700 mt-2">
                    Retirado por: <strong>{osEncontrada.retirada_por}</strong>
                  </p>
                )}
              </div>
            ) : (
              <form onSubmit={handleSubmitAtualizacao(onAtualizar)} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nome de quem está retirando *
                  </label>
                  <input
                    type="text"
                    {...registerAtualizacao('retirada_por', { required: true })}
                    className="input"
                    placeholder="Nome completo"
                  />
                </div>

                <div className="flex justify-end">
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={isAtualizando}
                    onClick={() => {
                      // Definir status como entregue ao cliente
                      const form = document.querySelector('form') as HTMLFormElement
                      const statusInput = document.createElement('input')
                      statusInput.type = 'hidden'
                      statusInput.name = 'status'
                      statusInput.value = 'ENTREGUE AO CLIENTE'
                      form.appendChild(statusInput)
                    }}
                  >
                    {isAtualizando ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Confirmando...
                      </>
                    ) : (
                      <>
                        <FileText className="h-4 w-4 mr-2" />
                        Confirmar Entrega
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  )
}