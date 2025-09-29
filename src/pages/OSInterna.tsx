import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Plus, FileText } from 'lucide-react'

interface OSInternaForm {
  secretaria: string
  setor: string
  solicitante: string
  telefone: string
  solicitacao_cliente: string
  categoria: string
  patrimonio: string
  equipamento: string
  tecnico: string
  data: string
  hora: string
}

const secretarias = [
  'CIDADANIA', 'CONTROLE INTERNO', 'CULTURA E ESPORTES', 'DESENVOLVIMENTO ECONÔMICO',
  'EDUCAÇÃO', 'FAZENDA', 'FORÇA POLICIAL', 'GOVERNO', 'INFRAESTRUTURA', 'OUTROS',
  'PROCURADORIA', 'SAÚDE', 'SEGURANÇA', 'SUSTENTABILIDADE'
]

const tecnicos = [
  'ABIMADÉSIO', 'ANTONY CAUÃ', 'DIEGO CARDOSO', 'DIEL BATISTA',
  'JOSAFÁ MEDEIROS', 'MAYKON RODOLFO', 'ROMÉRIO CIRQUEIRA', 'VALMIR FRANCISCO'
]

const categorias = [
  'CFTV', 'COMPUTADORES', 'IMPRESSORAS', 'OUTROS', 'REDES', 'SISTEMAS', 'TELEFONIA'
]

const equipamentos = [
  'CAMERA', 'CELULAR', 'COMPUTADOR', 'IMPRESSORA', 'MONITOR', 'NOBREAK',
  'NOTEBOOK', 'PERIFÉRICO', 'TABLET', 'TRANSFORMADOR', 'ROTEADOR', 'SISTEMA', 'SOFTWARE'
]

// Função para formatar telefone
const formatPhone = (value: string) => {
  const numbers = value.replace(/\D/g, '')
  if (numbers.length <= 10) {
    return numbers.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3')
  }
  return numbers.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3')
}

// Função para validar telefone
const validatePhone = (value: string) => {
  const numbers = value.replace(/\D/g, '')
  if (numbers.length === 10 || numbers.length === 11) {
    return true
  }
  return 'Telefone deve ter 10 ou 11 dígitos'
}
export default function OSInterna() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [phoneValue, setPhoneValue] = useState('')
  
  const { register, handleSubmit, reset, formState: { errors } } = useForm<OSInternaForm>({
    defaultValues: {
      data: new Date().toISOString().split('T')[0],
      hora: new Date().toTimeString().slice(0, 5),
    }
  })

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhone(e.target.value)
    setPhoneValue(formatted)
    e.target.value = formatted
  }
  const onSubmit = async (data: OSInternaForm) => {
    // Validar se todos os campos obrigatórios estão preenchidos
    if (!data.secretaria || data.secretaria === '') {
      alert('Por favor, selecione uma secretaria.')
      return
    }
    if (!data.categoria || data.categoria === '') {
      alert('Por favor, selecione uma categoria.')
      return
    }
    if (!data.equipamento || data.equipamento === '') {
      alert('Por favor, selecione um equipamento.')
      return
    }
    if (!data.tecnico || data.tecnico === '') {
      alert('Por favor, selecione um técnico.')
      return
    }

    setIsSubmitting(true)
    try {
      // Aqui será feita a chamada para a API
      console.log('Dados da OS Interna:', data)
      
      // Simular delay da API
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      alert('OS Interna registrada com sucesso!')
      setPhoneValue('')
      reset({
        data: new Date().toISOString().split('T')[0],
        hora: new Date().toTimeString().slice(0, 5),
      })
    } catch (error) {
      alert('Erro ao registrar OS Interna')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3">
        <FileText className="h-8 w-8 text-blue-600" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Ordem de Serviço Interna</h1>
          <p className="text-gray-600">Registre uma nova ordem de serviço interna</p>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold text-gray-900">Nova OS Interna</h2>
        </div>
        <div className="card-content">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Secretaria */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Secretaria *
                </label>
                <select
                  {...register('secretaria', { required: 'Secretaria é obrigatória' })}
                  className="input"
                >
                  <option value="">Selecione...</option>
                  {secretarias.map(secretaria => (
                    <option key={secretaria} value={secretaria}>{secretaria}</option>
                  ))}
                </select>
                {errors.secretaria && (
                  <p className="mt-1 text-sm text-red-600">{errors.secretaria.message}</p>
                )}
              </div>

              {/* Setor */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Setor *
                </label>
                <input
                  type="text"
                  {...register('setor', { required: 'Setor é obrigatório' })}
                  className="input"
                  placeholder="Digite o setor"
                />
                {errors.setor && (
                  <p className="mt-1 text-sm text-red-600">{errors.setor.message}</p>
                )}
              </div>

              {/* Solicitante */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Solicitante *
                </label>
                <input
                  type="text"
                  {...register('solicitante', { required: 'Solicitante é obrigatório' })}
                  className="input"
                  placeholder="Nome do solicitante"
                />
                {errors.solicitante && (
                  <p className="mt-1 text-sm text-red-600">{errors.solicitante.message}</p>
                )}
              </div>

              {/* Telefone */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Telefone *
                </label>
                <input
                  type="tel"
                  {...register('telefone', { 
                    required: 'Telefone é obrigatório',
                    validate: validatePhone
                  })}
                  className="input"
                  placeholder="(00) 00000-0000"
                  value={phoneValue}
                  onChange={handlePhoneChange}
                  maxLength={15}
                />
                {errors.telefone && (
                  <p className="mt-1 text-sm text-red-600">{errors.telefone.message}</p>
                )}
              </div>

              {/* Categoria */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Categoria do Serviço *
                </label>
                <select
                  {...register('categoria', { required: 'Categoria é obrigatória' })}
                  className="input"
                >
                  <option value="">Selecione...</option>
                  {categorias.map(categoria => (
                    <option key={categoria} value={categoria}>{categoria}</option>
                  ))}
                </select>
                {errors.categoria && (
                  <p className="mt-1 text-sm text-red-600">{errors.categoria.message}</p>
                )}
              </div>

              {/* Patrimônio */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Número do Patrimônio
                </label>
                <input
                  type="text"
                  {...register('patrimonio')}
                  className="input"
                  placeholder="Número do patrimônio"
                />
              </div>

              {/* Equipamento */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Equipamento *
                </label>
                <select
                  {...register('equipamento', { required: 'Equipamento é obrigatório' })}
                  className="input"
                >
                  <option value="">Selecione...</option>
                  {equipamentos.map(equipamento => (
                    <option key={equipamento} value={equipamento}>{equipamento}</option>
                  ))}
                </select>
                {errors.equipamento && (
                  <p className="mt-1 text-sm text-red-600">{errors.equipamento.message}</p>
                )}
              </div>

              {/* Técnico */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Técnico *
                </label>
                <select
                  {...register('tecnico', { required: 'Técnico é obrigatório' })}
                  className="input"
                >
                  <option value="">Selecione...</option>
                  {tecnicos.map(tecnico => (
                    <option key={tecnico} value={tecnico}>{tecnico}</option>
                  ))}
                </select>
                {errors.tecnico && (
                  <p className="mt-1 text-sm text-red-600">{errors.tecnico.message}</p>
                )}
              </div>

              {/* Data */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Data de Entrada *
                </label>
                <input
                  type="date"
                  {...register('data', { required: 'Data é obrigatória' })}
                  className="input"
                />
                {errors.data && (
                  <p className="mt-1 text-sm text-red-600">{errors.data.message}</p>
                )}
              </div>

              {/* Hora */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Hora de Entrada *
                </label>
                <input
                  type="time"
                  {...register('hora', { required: 'Hora é obrigatória' })}
                  className="input"
                />
                {errors.hora && (
                  <p className="mt-1 text-sm text-red-600">{errors.hora.message}</p>
                )}
              </div>
            </div>

            {/* Solicitação do Cliente */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Solicitação do Cliente *
              </label>
              <textarea
                {...register('solicitacao_cliente', { required: 'Solicitação é obrigatória' })}
                rows={4}
                className="input min-h-[100px] resize-y"
                placeholder="Descreva a solicitação do cliente..."
              />
              {errors.solicitacao_cliente && (
                <p className="mt-1 text-sm text-red-600">{errors.solicitacao_cliente.message}</p>
              )}
            </div>

            {/* Submit button */}
            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => {
                  reset()
                  setPhoneValue('')
                }}
                className="btn btn-outline"
                disabled={isSubmitting}
              >
                Limpar
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Registrando...
                  </>
                ) : (
                  <>
                    <Plus className="h-4 w-4 mr-2" />
                    Registrar OS
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}