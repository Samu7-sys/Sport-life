import http.server
import socketserver
import sqlite3
import hashlib
import secrets
from urllib.parse import parse_qs
from http import cookies

PORT = 8000
SESSIONS = {}  

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nome TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  cpf_cnpj TEXT UNIQUE NOT NULL,
                  senha TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(login, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    hashed = hash_password(password)
    c.execute("SELECT id, nome FROM users WHERE (email=? OR cpf_cnpj=?) AND senha=?", 
              (login, login, hashed))
    user = c.fetchone()
    conn.close()
    return user

def register_user(nome, email, cpf_cnpj, senha):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        hashed = hash_password(senha)
        c.execute("INSERT INTO users (nome, email, cpf_cnpj, senha) VALUES (?, ?, ?, ?)",
                  (nome, email, cpf_cnpj, hashed))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def get_session(self):
        cookie = cookies.SimpleCookie(self.headers.get('Cookie'))
        if 'session' in cookie:
            session_id = cookie['session'].value
            return SESSIONS.get(session_id)
        return None
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(302)
            self.send_header('Location', '/html/index.html')
            self.end_headers()
            return
        
        if self.path == '/html/index.html':
            try:
                with open('html/index.html', 'r', encoding='utf-8') as f:
                    html = f.read()
                
                session = self.get_session()
                if session:
                    html = html.replace('<a href="/html/login.html">Login</a>', 
                                       f'<a href="/logout">{session["nome"]}</a>')
                    html = html.replace('<a href="login.html">Login</a>', 
                                       f'<a href="/logout">{session["nome"]}</a>')
                    html = html.replace('href="/html/login.html"', 'href="/logout"')
                    html = html.replace('href="login.html"', 'href="/logout"')
                    html = html.replace('>Login</a>', f'>{session["nome"]}</a>')
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode())
                return
            except FileNotFoundError:
                pass
        
        if self.path == '/logout':
            cookie = cookies.SimpleCookie(self.headers.get('Cookie'))
            if 'session' in cookie:
                session_id = cookie['session'].value
                if session_id in SESSIONS:
                    del SESSIONS[session_id]
            
            self.send_response(302)
            self.send_header('Location', '/html/index.html')
            self.send_header('Set-Cookie', 'session=; Max-Age=0; Path=/')
            self.end_headers()
            return
        
        return super().do_GET()
    
    def do_POST(self):
        if self.path == '/login':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            data = parse_qs(post_data)
            
            login = data['login'][0]
            password = data['password'][0]
            
            user = verify_user(login, password)
            
            if user:
                session_id = secrets.token_urlsafe(32)
                SESSIONS[session_id] = {'id': user[0], 'nome': user[1].split()[0]}
                
                self.send_response(302)
                self.send_header('Location', '/html/index.html')
                self.send_header('Set-Cookie', f'session={session_id}; Path=/; Max-Age=86400')
                self.end_headers()
            else:
                html = '''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - ESPORT LIFE</title>
    <link rel="stylesheet" href="/css/login.css">
    <style>
        .error-message {
            background-color: #ff4444;
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 20px auto;
            text-align: center;
            max-width: 400px;
        }
    </style>
</head>
<body>
    <div class="error-message">
        ❌ Credenciais inválidas! Tente novamente.
    </div>
    <div class="login-container fade-in-up">
        <div class="logo">
            EL
            <span>ESPORT LIFE</span>
        </div>
        <div class="welcome-text">
            <h1>Que bom ter você aqui!</h1>
            <p>Entre e aproveite o melhor da ESPORT LIFE</p>
        </div>
        <form class="login-form" action="/login" method="POST">
            <div class="input-group">
                <label for="login">Informe CPF, CNPJ ou E-mail</label>
                <input type="text" id="login" name="login" placeholder="CPF,CNPJ ou e-mail" required>
            </div>
            <div class="input-group">
                <label for="password">Informe sua senha</label>
                <div class="password-input">
                    <input type="password" id="password" name="password" placeholder="Senha" required>
                    <span class="toggle-password"><i class="far fa-eye"></i></span>
                </div>
            </div>
            <div class="forgot-password">
                <a href="/html/cadastro.html">Não tem conta? aperte aqui</a>
            </div>
            <button type="submit" class="login-button">Entrar</button>
        </form>
        <div class="create-account">
            <a href="/html/cadastro.html" style="text-decoration: none;">
                <button type="button" class="create-account-button">Criar conta ESPORT LIFE</button>
            </a>
        </div>
        <div class="separator">
            <hr>
            <span>ou</span>
            <hr>
        </div>
        <button class="google-login">
            <i class="fab fa-google"></i>
            Entrar com o Google
        </button>
        <div class="help-link">
            <a href="#">Precisa de ajuda?</a>
        </div>
    </div>
    <div class="security-info">
        <i class="fas fa-lock"></i>
        Ambiente 100% seguro
    </div>
</body>
</html>'''
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode())
            return
        
        if self.path == '/register':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            data = parse_qs(post_data)
            
            nome = data['nome'][0]
            email = data['email'][0]
            cpf = data['cpf'][0]
            senha = data['senha'][0]
            confirmar = data['confirmarSenha'][0]
            
            if senha != confirmar:
                html = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Cadastro - ESPORT LIFE</title>
  <link rel="stylesheet" href="/css/cadastro.css" />
  <style>
    .error-message {
        background-color: #ff4444;
        color: white;
        padding: 15px;
        border-radius: 5px;
        margin: 20px auto;
        text-align: center;
        max-width: 400px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="error-message">
        ❌ As senhas não conferem! Tente novamente.
    </div>
    <div class="card">
      <h2>EL</h2>
      <p class="subtitulo">ESPORT LIFE</p>
      <h3>Crie sua conta!</h3>
      <p>Entre para aproveitar o melhor da ESPORT LIFE</p>
      <form action="/register" method="POST">
        <label for="nome">Nome completo</label>
        <input type="text" id="nome" name="nome" placeholder="Seu nome completo" required />
        <label for="email">E-mail</label>
        <input type="email" id="email" name="email" placeholder="Seu e-mail" required />
        <label for="cpf">CPF ou CNPJ</label>
        <input type="text" id="cpf" name="cpf" placeholder="Digite seu CPF ou CNPJ" required />
        <label for="senha">Senha</label>
        <input type="password" id="senha" name="senha" placeholder="Crie uma senha" required />
        <label for="confirmarSenha">Confirmar senha</label>
        <input type="password" id="confirmarSenha" name="confirmarSenha" placeholder="Confirme sua senha" required />
        <button type="submit" class="btn-entrar">Cadastrar</button>
      </form>
      <a href="/html/login.html" class="link">Já tem conta? Faça login</a>
      <hr />
      <button class="btn-google">Cadastrar com o Google</button>
      <a href="#" class="ajuda">Precisa de ajuda?</a>
    </div>
  </div>
</body>
</html>'''
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode())
                return
            
            if register_user(nome, email, cpf, senha):
                self.send_response(302)
                self.send_header('Location', '/html/login.html')
                self.end_headers()
            else:
                html = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Cadastro - ESPORT LIFE</title>
  <link rel="stylesheet" href="/css/cadastro.css" />
  <style>
    .error-message {
        background-color: #ff4444;
        color: white;
        padding: 15px;
        border-radius: 5px;
        margin: 20px auto;
        text-align: center;
        max-width: 400px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="error-message">
        ❌ Email ou CPF/CNPJ já cadastrado! Tente outro.
    </div>
    <div class="card">
      <h2>EL</h2>
      <p class="subtitulo">ESPORT LIFE</p>
      <h3>Crie sua conta!</h3>
      <p>Entre para aproveitar o melhor da ESPORT LIFE</p>
      <form action="/register" method="POST">
        <label for="nome">Nome completo</label>
        <input type="text" id="nome" name="nome" placeholder="Seu nome completo" required />
        <label for="email">E-mail</label>
        <input type="email" id="email" name="email" placeholder="Seu e-mail" required />
        <label for="cpf">CPF ou CNPJ</label>
        <input type="text" id="cpf" name="cpf" placeholder="Digite seu CPF ou CNPJ" required />
        <label for="senha">Senha</label>
        <input type="password" id="senha" name="senha" placeholder="Crie uma senha" required />
        <label for="confirmarSenha">Confirmar senha</label>
        <input type="password" id="confirmarSenha" name="confirmarSenha" placeholder="Confirme sua senha" required />
        <button type="submit" class="btn-entrar">Cadastrar</button>
      </form>
      <a href="/html/login.html" class="link">Já tem conta? Faça login</a>
      <hr />
      <button class="btn-google">Cadastrar com o Google</button>
      <a href="#" class="ajuda">Precisa de ajuda?</a>
    </div>
  </div>
</body>
</html>'''
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode())




if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("SERVIDOR ESPORT LIFE INICIADO")
    print("=" * 50)
    print(f"Endereço: http://localhost:{PORT}")

    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        httpd.serve_forever()