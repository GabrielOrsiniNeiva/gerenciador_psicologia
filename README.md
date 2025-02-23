# Sistema de Gerenciamento de Consultório Psicológico

## Descrição
Sistema web desenvolvido em Flask para gerenciamento de consultório psicológico, permitindo o controle de pacientes, agendamentos e pagamentos.

## Requisitos
- Python 3.11 ou superior
- PostgreSQL 16 ou superior
- pip (gerenciador de pacotes Python)

## Instalação

1. Clone o repositório:
   ```bash
   git clone <seu-repositorio>
   cd PsicologiaGestao
   ```

2. Instale o PostgreSQL:
   - Baixe e instale o PostgreSQL em: https://www.postgresql.org/download/windows/
   - Durante a instalação:
     - Anote a senha que você definir para o usuário postgres
     - Mantenha a porta padrão (5432)
   - Após a instalação, use o pgAdmin para criar um banco de dados chamado `psicologia_gestao`

3. Configure as variáveis de ambiente:
   - Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:
     ```
     DATABASE_URL=postgresql://postgres:SuaSenhaAqui@localhost:5432/psicologia_gestao
     SESSION_SECRET=sua_chave_secreta_aqui
     ```
   - Substitua `SuaSenhaAqui` pela senha do PostgreSQL
   - Altere `sua_chave_secreta_aqui` por uma string aleatória para segurança

4. Instale as dependências do projeto:
   ```bash
   python -m pip install -e .
   ```

5. Execute o sistema:
   ```bash
   python -m gerenciador_psicologia.main
   ```

O servidor iniciará em http://localhost:5000

## Estrutura do Projeto

### Pacote Principal (`gerenciador_psicologia/`)
- `__init__.py`: Inicialização do pacote
- `app.py`: Configuração da aplicação Flask e banco de dados
- `models.py`: Modelos de dados SQLAlchemy
- `main.py`: Rotas e lógica de negócio

### Templates (`gerenciador_psicologia/templates/`)
- `/appointments`: Templates relacionados a consultas
- `/financial`: Templates para gestão financeira
- `/patients`: Templates de gestão de pacientes
- `base.html`: Template base com layout comum

### Arquivos Estáticos (`gerenciador_psicologia/static/`)
- `/css`: Estilos CSS customizados
- `/js`: Scripts JavaScript

### Arquivos de Configuração
- `pyproject.toml`: Configuração do projeto e dependências
- `.env`: Variáveis de ambiente (não versionado)

## Funcionalidades

### Pacientes
- Cadastro de pacientes
- Listagem com busca
- Edição de dados
- Visualização de detalhes

### Consultas
- Agendamento de consultas
- Consultas recorrentes (semanal, quinzenal, mensal)
- Cancelamento
- Histórico por paciente

### Financeiro
- Registro de pagamentos
- Relatório financeiro
- Controle de valores recebidos
- Histórico de transações

## Desenvolvimento

Para contribuir com o projeto:

1. Crie um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nome-da-feature`)
3. Faça commit das mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nome-da-feature`)
5. Crie um Pull Request

## Licença
Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Suporte
Para reportar bugs ou sugerir melhorias, abra uma issue no repositório do projeto.
