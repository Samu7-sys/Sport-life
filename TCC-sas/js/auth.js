// ============================================
// ARQUIVO: js/auth.js
// Sistema de Autenticação Firebase
// ============================================

import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js';
import { 
    getAuth, 
    createUserWithEmailAndPassword, 
    signInWithEmailAndPassword,
    GoogleAuthProvider, 
    signInWithPopup, 
    updateProfile,
    onAuthStateChanged,
    signOut 
} from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js';
import { 
    getDatabase, 
    ref, 
    set 
} from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-database.js';

// Configuração do Firebase
const firebaseConfig = {
    apiKey: "AIzaSyBBJFIx3eAIa6YS598N0AKM2tGzqIiJCFg",
    authDomain: "esportlife-d3121.firebaseapp.com",
    databaseURL: "https://esportlife-d3121-default-rtdb.firebaseio.com",
    projectId: "esportlife-d3121",
    storageBucket: "esportlife-d3121.firebasestorage.app",
    messagingSenderId: "669330554548",
    appId: "1:669330554548:web:d0b115a768e7ff4265e1e1",
    measurementId: "G-GLEW76YDRX"
};

// Inicializa Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const database = getDatabase(app);

// ============================================
// FUNÇÕES AUXILIARES
// ============================================

function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    if (!messageDiv) return;
    
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.style.display = 'block';
    
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
}

function getErrorMessage(errorCode) {
    const errorMessages = {
        'auth/email-already-in-use': 'Este e-mail já está em uso!',
        'auth/invalid-email': 'E-mail inválido!',
        'auth/weak-password': 'Senha muito fraca! Use no mínimo 6 caracteres.',
        'auth/user-not-found': 'Usuário não encontrado!',
        'auth/wrong-password': 'Senha incorreta!',
        'auth/too-many-requests': 'Muitas tentativas. Tente novamente mais tarde.',
        'auth/network-request-failed': 'Erro de conexão. Verifique sua internet.',
        'auth/popup-closed-by-user': 'Login com Google cancelado.'
    };
    
    return errorMessages[errorCode] || 'Erro ao processar solicitação. Tente novamente.';
}

// ============================================
// CADASTRO
// ============================================

export async function handleCadastro(e) {
    e.preventDefault();
    
    const nome = document.getElementById('nome').value.trim();
    const email = document.getElementById('email').value.trim();
    const senha = document.getElementById('senha').value;
    const confirmarSenha = document.getElementById('confirmarSenha').value;

    // Validações
    if (senha !== confirmarSenha) {
        showMessage('As senhas não coincidem!', 'error');
        return;
    }

    if (senha.length < 6) {
        showMessage('A senha deve ter no mínimo 6 caracteres!', 'error');
        return;
    }

    if (!nome) {
        showMessage('Por favor, preencha seu nome!', 'error');
        return;
    }

    try {
        // Cria usuário no Firebase Auth
        const userCredential = await createUserWithEmailAndPassword(auth, email, senha);
        const user = userCredential.user;

        // Atualiza o perfil com o nome
        await updateProfile(user, {
            displayName: nome
        });

        // Salva dados adicionais no Realtime Database
        await set(ref(database, 'users/' + user.uid), {
            nome: nome,
            email: email,
            dataCadastro: new Date().toISOString(),
            provider: 'email'
        });

        showMessage('✅ Cadastro realizado com sucesso! Redirecionando...', 'success');
        
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 2000);

    } catch (error) {
        console.error('Erro no cadastro:', error);
        showMessage(getErrorMessage(error.code), 'error');
    }
}

// ============================================
// LOGIN
// ============================================

export async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    if (!email || !password) {
        showMessage('Preencha todos os campos!', 'error');
        return;
    }

    try {
        await signInWithEmailAndPassword(auth, email, password);
        showMessage('✅ Login realizado! Redirecionando...', 'success');
        
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1500);

    } catch (error) {
        console.error('Erro no login:', error);
        showMessage(getErrorMessage(error.code), 'error');
    }
}

// ============================================
// LOGIN COM GOOGLE
// ============================================

export async function handleGoogleSignIn() {
    const provider = new GoogleAuthProvider();
    
    try {
        const result = await signInWithPopup(auth, provider);
        const user = result.user;

        // Salva ou atualiza dados no database
        await set(ref(database, 'users/' + user.uid), {
            nome: user.displayName,
            email: user.email,
            dataCadastro: new Date().toISOString(),
            provider: 'google',
            photoURL: user.photoURL || null
        });

        showMessage('✅ Login com Google realizado! Redirecionando...', 'success');
        
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1500);

    } catch (error) {
        console.error('Erro no login com Google:', error);
        if (error.code !== 'auth/popup-closed-by-user') {
            showMessage(getErrorMessage(error.code), 'error');
        }
    }
}

// ============================================
// LOGOUT
// ============================================

export async function handleLogout() {
    try {
        await signOut(auth);
        window.location.href = 'login.html';
    } catch (error) {
        console.error('Erro ao fazer logout:', error);
        alert('Erro ao sair. Tente novamente.');
    }
}

// ============================================
// VERIFICAR ESTADO DE AUTENTICAÇÃO
// ============================================

export function checkAuthState() {
    onAuthStateChanged(auth, (user) => {
        const currentPage = window.location.pathname;
        const publicPages = ['/login.html', '/cadastro.html', '/suporte.html'];
        const isPublicPage = publicPages.some(page => currentPage.includes(page));

        if (user) {
            // Usuário logado
            console.log('Usuário logado:', user.email);
            
            // Atualiza nome do usuário na página
            const userNameDisplay = document.getElementById('userNameDisplay');
            if (userNameDisplay) {
                userNameDisplay.textContent = `Olá, ${user.displayName || 'Usuário'}!`;
            }
            
            // Se estiver na página de login/cadastro, redireciona
            if (isPublicPage && !currentPage.includes('suporte')) {
                window.location.href = 'index.html';
            }
        } else {
            // Usuário não logado
            console.log('Usuário não logado');
            
            // Se não estiver em página pública, redireciona para login
            if (!isPublicPage) {
                window.location.href = 'login.html';
            }
        }
    });
}

// ============================================
// EXPORTAÇÕES
// ============================================

export { auth, database };