# ENEM Question Processor

Este projeto utiliza o Google ADK (Agent Development Kit) para processar questões do ENEM, buscando informações no Google e YouTube, e retornando um JSON formatado com respostas e links relevantes.

## Recursos

- Processamento de questões do ENEM em formato estruturado
- Busca de informações no Google (até 3 resultados)
- Extração eficiente de conteúdo web com fetch MCP
- Busca de vídeos no YouTube relacionados à questão
- API REST com FastAPI para integração com outros sistemas

## Requisitos

- Python 3.9+
- Google API Key
- SERP API Key (para busca no Google e YouTube)
- MCP fetch configurado para extração de conteúdo web

## Instalação

1. Clone o repositório:
```
git clone https://github.com/seu-usuario/genem.git
cd genem
```

2. Instale as dependências:
```
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
```
export GOOGLE_API_KEY="sua-chave-da-api-do-google"
export SERP_API_KEY="sua-chave-da-api-serpapi"
```

4. Configure o MCP fetch server:
```
npx mcp-fetch
```

## Uso

### Via API REST

1. Inicie o servidor:
```
python app.py
```

2. Acesse a documentação da API em `http://localhost:8000/docs`

3. Envie uma requisição POST para `/process-question` com o seguinte formato:
```json
{
  "title": "Questão 35 ENEM 2022",
  "discipline": "Matemática",
  "context": "Um modelo matemático para determinar a energia consumida...",
  "ano": "2022",
  "alternativas": "a) 10^-4 \nb) 2 × 10^-4 \nc) 4 × 10^-4 \nd) 2 × 10^-3 \ne) 4 × 10^-3",
  "alternativaCorreta": "b) 2 × 10^-4"
}
```

### Via Script Python

Execute o script de teste para processar uma questão de exemplo:
```
python -m adk_test.search.test_enem_agent
```

## Formato de Resposta

O sistema retorna um JSON com o seguinte formato:

```json
{
  "referenceQuestion": "Questão 35 ENEM 2022",
  "answers": [
    {
      "response": "Texto explicativo baseado no conteúdo da página",
      "link": "URL da página"
    }
  ],
  "videoLinks": [
    {
      "title": "Título do vídeo",
      "link": "URL do vídeo"
    }
  ]
}
```

## Estrutura do Projeto

- `/adk_test/search/` - Módulos principais
  - `google_mcp_tool.py` - Ferramenta para busca no Google
  - `youtube_mcp_tool.py` - Ferramenta para busca no YouTube
  - `fetch_tool.py` - Ferramenta para extração eficiente de conteúdo web com fetch MCP
  - `enem_agent.py` - Agente principal para processamento de questões
  - `test_enem_agent.py` - Script de teste
- `app.py` - Servidor FastAPI

## Licença

MIT
