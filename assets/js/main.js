/* =====================================
   SICRAI - MAIN JS
===================================== */

// MENU MOBILE
// Cria o ícone do menu automaticamente se a página não tiver um,
// assim todas as páginas públicas funcionam sem mexer no HTML.
(function iniciarMenuMobile() {

    const navbar = document.querySelector(".navbar");
    const navLinks = document.querySelector(".nav-links");

    if (!navbar || !navLinks) return;

    let menuBtn = document.querySelector(".menu-mobile");

    if (!menuBtn) {
        menuBtn = document.createElement("div");
        menuBtn.className = "menu-mobile";
        menuBtn.innerHTML = '<i class="fa-solid fa-bars"></i>';
        navbar.appendChild(menuBtn);
    }

    menuBtn.setAttribute("role", "button");
    menuBtn.setAttribute("tabindex", "0");
    menuBtn.setAttribute("aria-label", "Abrir menu");

    // Leva os botões Entrar / Cadastrar (escondidos no mobile) para dentro do menu
    const navButtons = document.querySelector(".nav-buttons");

    if (navButtons) {
        navButtons.querySelectorAll("a").forEach(link => {
            const li = document.createElement("li");
            li.className = "nav-mobile-only";

            const copia = link.cloneNode(true);
            li.appendChild(copia);

            navLinks.appendChild(li);
        });
    }

    function definirMenu(aberto) {
        navLinks.classList.toggle("active", aberto);
        menuBtn.innerHTML = aberto
            ? '<i class="fa-solid fa-xmark"></i>'
            : '<i class="fa-solid fa-bars"></i>';
        menuBtn.setAttribute("aria-label", aberto ? "Fechar menu" : "Abrir menu");
    }

    menuBtn.addEventListener("click", () => {
        definirMenu(!navLinks.classList.contains("active"));
    });

    menuBtn.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            definirMenu(!navLinks.classList.contains("active"));
        }
    });

    // Fecha ao clicar em um link
    navLinks.addEventListener("click", (e) => {
        if (e.target.closest("a")) definirMenu(false);
    });

    // Fecha ao aumentar a tela
    window.addEventListener("resize", () => {
        if (window.innerWidth > 850) definirMenu(false);
    });

})();

// ANIMAÇÃO AO SCROLL
const observer = new IntersectionObserver((entries) => {

    entries.forEach(entry => {

        if(entry.isIntersecting){

            entry.target.classList.add("show");

        }

    });

},{
    threshold:0.2
});

document.querySelectorAll(
".benefit-card, .step-card, .glass-card"
).forEach(el => {

    observer.observe(el);

});

// SAUDAÇÃO AUTOMÁTICA
function saudacao(){

    const hora = new Date().getHours();

    if(hora < 12){
        return "Bom dia";
    }

    if(hora < 18){
        return "Boa tarde";
    }

    return "Boa noite";

}

const saudacaoElemento =
document.getElementById("saudacao");

if(saudacaoElemento){

    saudacaoElemento.innerHTML =
    `${saudacao()}, seja bem-vindo ao SICRAI!`;

}

// CONTADOR ANIMADO
function animarNumero(id, valorFinal){

    const elemento =
    document.getElementById(id);

    if(!elemento) return;

    let atual = 0;

    const incremento =
    Math.ceil(valorFinal / 80);

    const intervalo = setInterval(() => {

        atual += incremento;

        if(atual >= valorFinal){

            atual = valorFinal;

            clearInterval(intervalo);

        }

        elemento.textContent =
        atual.toLocaleString("pt-BR");

    },20);

}

// EXEMPLOS
animarNumero("contadorPontos",2450);
animarNumero("contadorLatas",245);

// BOTÃO VOLTAR AO TOPO
const botaoTopo =
document.createElement("button");

botaoTopo.innerHTML =
'<i class="fa-solid fa-arrow-up"></i>';

botaoTopo.classList.add("btn-top");
botaoTopo.setAttribute("aria-label", "Voltar ao topo");

document.body.appendChild(botaoTopo);

window.addEventListener("scroll", () => {

    if(window.scrollY > 300){

        botaoTopo.classList.add("visivel");

    }else{

        botaoTopo.classList.remove("visivel");

    }

});

botaoTopo.addEventListener("click", () => {

    window.scrollTo({
        top:0,
        behavior:"smooth"
    });

});

// DARK MODE
const darkButton =
document.getElementById("toggleDark");

if(darkButton){

    darkButton.addEventListener("click", () => {

        document.body.classList.toggle("dark");

        localStorage.setItem(
            "tema",
            document.body.classList.contains("dark")
            ? "dark"
            : "light"
        );

    });

}

window.addEventListener("load", () => {

    const tema =
    localStorage.getItem("tema");

    if(tema === "dark"){

        document.body.classList.add("dark");

    }

});