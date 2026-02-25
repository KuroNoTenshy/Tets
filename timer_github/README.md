# Timer App — Build Guide

## Como gerar o Timer.exe gratuitamente com GitHub Actions

### Passo 1 — Criar conta GitHub
Vai a https://github.com e cria uma conta gratuita (se ainda não tiveres).

### Passo 2 — Criar repositório
1. Clica em **"New repository"** (botão verde)
2. Nome: `timer-app` (ou qualquer nome)
3. Deixa em **Public**
4. Clica **"Create repository"**

### Passo 3 — Fazer upload dos ficheiros
Clica em **"uploading an existing file"** e faz upload de:
- `timer.py`
- `.github/workflows/build.yml`  ← (tens de criar esta pasta manualmente no upload)

**Forma mais fácil:** usa o GitHub Desktop ou arrasta os ficheiros.

### Passo 4 — A build corre automaticamente!
Assim que fizeres o upload, o GitHub compila automaticamente.

### Passo 5 — Descarregar o .exe
1. Vai ao separador **"Actions"** no teu repositório
2. Clica na build mais recente
3. Em baixo em **"Artifacts"**, clica em **"Timer-Windows-x64"**
4. Descarrega o ZIP, extrai → tens o `Timer.exe` pronto!
