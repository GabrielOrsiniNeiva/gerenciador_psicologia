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
   pip install -r requirements.txt
   ```

5. Execute o sistema:
   ```bash
   python run.py
   ```

O servidor iniciará em http://localhost:5000

## Estrutura do Projeto

### Pacote Principal (`gerenciador_psicologia/`)
- `__init__.py`: Inicialização do pacote
- `app.py`: Fábrica de aplicação (Application Factory) e configuração do Flask
- `models.py`: Modelos de dados SQLAlchemy
- `extensions.py`: Inicialização de extensões do Flask (ex: SQLAlchemy)
- `main.py`: Blueprint principal (contém a rota de entrada `/`)
- `routes/`: Módulo contendo os Blueprints da aplicação
  - `dashboard.py`: Rota para a página de dashboard
  - `patients.py`: Rotas para o gerenciamento de pacientes
  - `appointments.py`: Rotas para o gerenciamento de consultas
  - `financial.py`: Rotas para o gerenciamento financeiro

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

### Dashboard
- Visualização de indicadores chave (KPIs) como total de pagamentos, despesas, lucro e número de pacientes ativos.
- Gráfico com a visão geral financeira mensal, comparando receitas e despesas.

## Guia de Desenvolvimento

Este documento descreve os principais aprendizados e o fluxo de trabalho para realizar alterações no projeto.

### 1. Estrutura e Configuração

- **Application Factory**: O projeto utiliza o padrão "Application Factory". A instância da aplicação Flask é criada pela função `create_app()` no arquivo `gerenciador_psicologia/app.py`.
- **Dependências**: As dependências Python são gerenciadas pelo arquivo `requirements.txt`. Para instalar ou atualizar, use:
  ```bash
  pip install -r requirements.txt
  ```
- **Variáveis de Ambiente**: A configuração é carregada de variáveis de ambiente.
  - **`.env`**: Armazena segredos e configurações de ambiente (ex: `DATABASE_URL`, `SESSION_SECRET`).
  - **`.flaskenv`**: Configura o ambiente do Flask CLI. É crucial que `FLASK_APP` aponte para a factory da aplicação: `FLASK_APP=gerenciador_psicologia.app`.

### 2. Banco de Dados e Migrações

O esquema do banco de dados é gerenciado com **Flask-Migrate** (Alembic). Qualquer alteração nos modelos (`gerenciador_psicologia/models.py`) deve ser acompanhada de uma migração.

#### Fluxo de Trabalho para Alterar o Banco de Dados:

1.  **Modifique o Modelo**: Faça as alterações necessárias no arquivo `gerenciador_psicologia/models.py` (ex: adicionar uma coluna, alterar um tipo de dado).
    - **Dica**: Para campos com valores restritos (como status), prefira usar `db.Enum('valor1', 'valor2', name='nome_do_enum')` para garantir consistência entre a aplicação e o banco de dados.

2.  **Gere o Script de Migração**: Com o ambiente virtual ativado, execute o comando `migrate`. Ele irá comparar os modelos com o estado atual do banco de dados e gerar um script de migração.
    ```bash
    flask db migrate -m "Descrição curta da alteração"
    ```

3.  **Aplique a Migração**: Execute o comando `upgrade` para aplicar o script gerado ao banco de dados.
    ```bash
    flask db upgrade
    ```

#### Solução de Problemas de Migração:

- **`No changes in schema detected`**: Se o Alembic não detectar uma alteração (especialmente em tipos de dados como `ENUM`), pode ser necessário criar uma migração manual.
- **Inconsistências no Histórico**: Se ocorrerem erros sobre "revisões não encontradas", pode indicar uma dessincronização entre os arquivos de migração locais e a tabela `alembic_version` no banco de dados. A solução mais drástica, mas eficaz, é apagar a tabela `alembic_version` e recriar as migrações do zero (cuidado em produção).

### 3. Executando a Aplicação

Para iniciar o servidor de desenvolvimento local, use o script `run.py`:

```bash
python run.py
```

Isso utilizará as configurações definidas nos arquivos `.env` e `.flaskenv`.

## Como Contribuir

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
