```javascript
"use strict";

/**
 * ============================================================
 * AUTH GUARD
 * Facebook Social Media Analytics Platform
 * ============================================================
 *
 * Funções:
 * - Verifica a sessão do utilizador.
 * - Redireciona utilizadores não autenticados para o login.
 * - Evita verificações repetidas durante a mesma página.
 * - Trata erros de rede e respostas inesperadas.
 * - Permite acesso à página de login sem autenticação.
 * ============================================================
 */

(function () {
    const LOGIN_PAGE = "/login.html";
    const SESSION_ENDPOINT = "/api/v1/auth/me";

    const currentPath = window.location.pathname.toLowerCase();

    // A página de login deve permanecer pública.
    if (currentPath === LOGIN_PAGE) {
        return;
    }

    // Evita executar o guard dentro de páginas incorporadas.
    if (window.self !== window.top) {
        return;
    }

    async function verifySession() {
        try {
            const response = await fetch(SESSION_ENDPOINT, {
                method: "GET",
                credentials: "same-origin",
                headers: {
                    Accept: "application/json"
                },
                cache: "no-store",
                redirect: "follow"
            });

            // Sessão inexistente ou expirada.
            if (response.status === 401) {
                redirectToLogin();
                return;
            }

            // O servidor pode estar indisponível ou ter outro erro.
            if (!response.ok) {
                console.error(
                    "Falha ao verificar a sessão. HTTP:",
                    response.status
                );
                showConnectionError();
                return;
            }

            const user = await response.json();

            if (!user || !user.id || !user.username) {
                console.error("Resposta de sessão inválida.");
                redirectToLogin();
                return;
            }

            // Disponibiliza os dados básicos do utilizador
            // para outros scripts da aplicação.
            window.currentUser = user;

            document.documentElement.classList.add("authenticated");

            window.dispatchEvent(
                new CustomEvent("auth:authenticated", {
                    detail: { user }
                })
            );

        } catch (error) {
            console.error(
                "Não foi possível verificar a sessão:",
                error
            );

            showConnectionError();
        }
    }

    function redirectToLogin() {
        if (window.location.pathname.toLowerCase() === LOGIN_PAGE) {
            return;
        }

        const returnUrl =
            window.location.pathname +
            window.location.search +
            window.location.hash;

        const loginUrl = new URL(LOGIN_PAGE, window.location.origin);

        // Guarda apenas o caminho interno para voltar após login.
        loginUrl.searchParams.set("next", returnUrl);

        window.location.replace(loginUrl.pathname + loginUrl.search);
    }

    function showConnectionError() {
        document.documentElement.classList.add("auth-check-failed");

        // O erro de rede não significa necessariamente
        // que a sessão expirou. Não redirecionamos automaticamente.
        if (!document.getElementById("authConnectionError")) {
            const notice = document.createElement("div");

            notice.id = "authConnectionError";
            notice.setAttribute("role", "alert");
            notice.textContent =
                "Não foi possível verificar a sessão. " +
                "Verifique a ligação ao servidor e recarregue a página.";

            Object.assign(notice.style, {
                position: "fixed",
                top: "16px",
                left: "16px",
                right: "16px",
                zIndex: "99999",
                padding: "14px 18px",
                background: "#fff4e5",
                color: "#7a4100",
                border: "1px solid #ffd59a",
                borderRadius: "8px",
                fontSize: "14px",
                fontFamily: "Arial, sans-serif",
                boxShadow: "0 4px 14px rgba(0,0,0,0.12)"
            });

            document.body.prepend(notice);
        }
    }

    // Executa a verificação da sessão.
    verifySession();
})();
```