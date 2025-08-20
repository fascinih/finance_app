# 🚀 Finance App - Início Rápido

## ⚡ Instalação em 5 Minutos

### 1. Pré-requisitos
```bash
# Ubuntu 20.04+ com Python 3.9+
python3 --version
```

### 2. Download e Setup
```bash
# Clonar o projeto (substitua pela URL real)
git clone <repository-url>
cd finance_app

# Executar instalação automática
chmod +x scripts/setup_ubuntu.sh
sudo ./scripts/setup_ubuntu.sh
```

### 3. Configurar Banco de Dados
```bash
# Setup do PostgreSQL
chmod +x scripts/setup_database.sh
./scripts/setup_database.sh
```

### 4. Iniciar Aplicação
```bash
# Iniciar todos os serviços
chmod +x scripts/start_all.sh
./scripts/start_all.sh
```

### 5. Acessar Interface
- **Interface Web**: http://localhost:8501
- **API Backend**: http://localhost:8000/docs

## 🎯 Primeiros Passos

### 1. Gerar Dados de Exemplo
```bash
# Criar 1000 transações sintéticas
python scripts/generate_sample_data.py --transactions 1000

# Importar via interface web ou API
```

### 2. Configurar IA (Opcional)
```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Baixar modelo
ollama pull llama2

# Configurar
./scripts/configure_ollama.sh
```

### 3. Importar Seus Dados
1. Acesse http://localhost:8501
2. Vá para "📤 Import"
3. Baixe o template CSV
4. Preencha com seus dados
5. Faça upload

### 4. Explorar Analytics
1. Vá para "📊 Analytics"
2. Explore padrões de gastos
3. Veja tendências mensais
4. Analise categorias

## 🛠️ Comandos Úteis

```bash
# Parar todos os serviços
./scripts/stop_all.sh

# Monitorar sistema
./scripts/monitor_system.sh

# Backup do banco
./scripts/backup_database.sh

# Ver logs
tail -f /var/log/finance_app/*.log

# Gerar mais dados de teste
python scripts/generate_sample_data.py --transactions 5000 --days 730
```

## 🔧 Solução Rápida de Problemas

### Serviço não inicia?
```bash
# Verificar status
./scripts/monitor_system.sh

# Reiniciar tudo
./scripts/stop_all.sh
./scripts/start_all.sh
```

### Banco não conecta?
```bash
# Verificar PostgreSQL
sudo systemctl status postgresql

# Reconfigurar se necessário
./scripts/setup_database.sh
```

### Interface não carrega?
```bash
# Verificar porta
netstat -tuln | grep 8501

# Verificar logs
tail -f /var/log/finance_app/streamlit.log
```

## 📱 Uso Básico

### Importar Transações
1. **CSV**: Use o template fornecido
2. **Excel**: Qualquer planilha com colunas: data, valor, descrição
3. **OFX**: Arquivo do seu banco

### Categorizar Automaticamente
1. Configure o Ollama (IA)
2. As transações serão categorizadas automaticamente
3. Ajuste manualmente se necessário

### Ver Analytics
1. **Dashboard**: Visão geral
2. **Analytics**: Análises detalhadas
3. **Padrões**: Gastos recorrentes
4. **Tendências**: Evolução temporal

## 🎉 Pronto!

Sua Finance App está funcionando! 

- ✅ Interface web em http://localhost:8501
- ✅ API em http://localhost:8000
- ✅ Dados de exemplo carregados
- ✅ IA configurada (se Ollama instalado)

**Próximo passo**: Importe seus dados reais e explore os insights!

