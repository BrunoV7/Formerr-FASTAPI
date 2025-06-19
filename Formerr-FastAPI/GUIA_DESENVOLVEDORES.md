# Guia para Desenvolvedores Iniciantes - Formerr API

Bem-vindos à equipe! 👋

Este guia vai ajudar vocês a entender e contribuir com o projeto Formerr API.

## 🎯 O que é o Formerr?

O Formerr é uma API para criar e gerenciar formulários online. Imagine um "Google Forms" profissional com funcionalidades avançadas.

## 🧭 Por onde começar?

### 1. **Primeiro, entenda a estrutura:**

```
main.py                 ← Arquivo principal (comece por aqui!)
app/
├── config.py          ← Configurações (senhas, URLs, etc.)
├── dependencies.py    ← Funções que verificam autenticação
├── auth/              ← Tudo sobre login/logout
├── forms/             ← Criar e gerenciar formulários
├── public/            ← APIs que não precisam de login
└── ...
```

### 2. **Leia os arquivos nesta ordem:**

1. `main.py` - Entenda como a aplicação inicia
2. `app/config.py` - Veja como as configurações funcionam
3. `app/dependencies.py` - Aprenda sobre autenticação
4. `app/public/routes.py` - Rotas simples (sem autenticação)
5. `app/auth/routes.py` - Sistema de login

## 💡 Conceitos importantes

### FastAPI - O que é?

FastAPI é como o Flask, mas:
- ✅ Mais rápido
- ✅ Documentação automática
- ✅ Validação automática de dados
- ✅ Type hints (dicas de tipo)

### Dependencies - O que são?

Dependencies são funções que rodam antes das suas rotas. Exemplo:

```python
# Esta função verifica se o usuário está logado
async def get_current_user(request: Request):
    # ... código de verificação ...
    return user_data

# Esta rota SÓ funciona se o usuário estiver logado
@app.get("/meu-perfil")
async def meu_perfil(user = Depends(get_current_user)):
    return {"nome": user["name"]}
```

### JWT Token - O que é?

JWT é como um "cartão de identidade digital":
- Usuário faz login → recebe um token
- A cada requisição → envia o token
- API verifica o token → permite ou nega acesso

## 🛠️ Como contribuir?

### 1. **Configure seu ambiente:**

```bash
# Clone o projeto
git clone <url>
cd Formerr-FastAPI

# Crie ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# ou
.venv\\Scripts\\activate   # Windows

# Instale dependências
pip install -r requirements.txt

# Configure o .env (peça as credenciais para o BrunoV7)
cp .env.example .env

# Rode a aplicação
python main.py
```

### 2. **Teste se funcionou:**

- Abra: http://localhost:8000
- Deve aparecer: `{"message": "Formerr API funcionando corretamente"}`
- Abra: http://localhost:8000/docs
- Deve aparecer: Documentação interativa

### 3. **Sua primeira contribuição:**

Comece com algo simples, como:
- Adicionar um endpoint GET simples
- Melhorar uma mensagem de erro
- Adicionar comentários em código
- Criar um teste básico

## 📚 Estudem estes conceitos:

### Python/FastAPI:
- Type hints (`def funcao(nome: str) -> dict:`)
- Async/await (`async def` e `await`)
- Decorators (`@app.get("/rota")`)
- Pydantic models (validação de dados)

### HTTP/APIs:
- Métodos: GET, POST, PUT, DELETE
- Status codes: 200, 401, 404, 500
- Headers (especialmente Authorization)
- JSON request/response

### Banco de dados:
- SQL básico (SELECT, INSERT, UPDATE, DELETE)
- SQLAlchemy (ORM do Python)
- Migrations (Alembic)

## 🔍 Como debuggar?

### 1. **Leia os logs:**
Quando algo der erro, olhe o terminal onde rodou `python main.py`

### 2. **Use a documentação:**
Vá em http://localhost:8000/docs e teste os endpoints

### 3. **Use print() temporariamente:**
```python
@app.get("/teste")
async def teste():
    print("Chegou aqui!")  # Para debuggar
    return {"ok": True}
```

### 4. **Teste com curl:**
```bash
# Teste básico
curl http://localhost:8000/

# Teste com dados
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"nome": "teste"}' \
  http://localhost:8000/api/endpoint
```

## 📝 Tarefas para praticar:

### Nível Iniciante:
1. Adicione um endpoint `GET /api/version` que retorna a versão da API
2. Modifique o endpoint `/health` para incluir a hora atual
3. Crie um endpoint `GET /api/status` que retorna se tudo está OK

### Nível Intermediário:
1. Crie um endpoint que recebe um nome e retorna "Olá, [nome]!"
2. Adicione validação para não aceitar nomes vazios
3. Faça um endpoint que calcula a idade baseado no ano de nascimento

### Nível Avançado:
1. Crie um sistema simples de "favoritos" (sem banco)
2. Implemente cache em memória para algum endpoint
3. Adicione logs estruturados com timestamp

## 🆘 Quando pedir ajuda?

Peçam ajuda quando:
- ❌ Não conseguirem rodar a aplicação
- ❌ Não entenderem um erro
- ❌ Não souberem como implementar algo
- ❌ Tiverem dúvidas sobre a arquitetura

**Não peçam ajuda quando:**
- ✅ For algo que podem pesquisar no Google
- ✅ For conceito básico de Python
- ✅ For possível resolver lendo a documentação

## 🎁 Dicas extras:

1. **Usem a documentação:** http://localhost:8000/docs é muito útil!
2. **Leiam o código:** Todo código tem comentários em português
3. **Testem sempre:** Após fazer mudanças, testem se ainda funciona
4. **Git:** Façam commits pequenos e descritivos
5. **Code review:** Sempre peçam para alguém revisar o código

## 📞 Contatos:

- **Dúvidas técnicas:** BrunoV7
- **Dúvidas de negócio:** BrunoV7
- **Problemas com ambiente:** BrunoV7

---

**Lembrem-se:** Todo mundo já foi iniciante um dia. Não tenham medo de errar ou perguntar! 🚀

**Boa sorte e bem-vindos à equipe!** 🎉
