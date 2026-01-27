// ---------- left Sidebar js -------------------

$(document).on('click','#sidebar li', function(){
    $(this).addClass('active').siblings().removeClass('active')
});

// ---------- left Sidebar js -------------------

$('.sub-menu ul').hide();
$(".sub-menu a").click(function(){
    $(this).parent(".sub-menu").children("ul").slideToggle("100");
    $(this).find(".right").toggleClass("fa-caret-up fa-caret-down");
});

// ---------------- Sidebar toggle ----------------

$(document).ready(function(){
    $("#toggleSidebar").click(function(){
        $(".left-menu").toggleClass("hide");
        $(".content-wrapper").toggleClass("hide");
    });
});

// ----------------  Table ----------------

$(document).ready(function(){
    $('#table-p3').DataTable();

});

document.addEventListener("DOMContentLoaded", function() {
    carregarDadosDashboard();
});

//

async function carregarDadosDashboard() {
    try {
        // Chama a API criada em Python
        const response = await fetch('/api/dashboard/resumo');
        const data = await response.json();

        if (data.cards) {
            // Função formatadora de moeda BRL
            const fmt = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

            // Atualiza os Cards (Texto)
            document.getElementById('card-custo-mensal').innerText = fmt.format(data.cards.custo_mensal);
            document.getElementById('card-perda-mensal').innerText = fmt.format(data.cards.perda_mensal);
            // Adicione os IDs correspondentes no seu HTML para os outros cards
        }

        // Renderiza o Gráfico de Custo (Chart.js)
        renderizarGraficoBarras('custo-mensal-1', data.grafico_custo_loja.labels, data.grafico_custo_loja.values, 'Custo por Loja');
        
        // Renderiza o Gráfico de Perdas (Chart.js)
        renderizarGraficoBarras('chartDezMaisPerdas', data.grafico_top_perdas.labels, data.grafico_top_perdas.values, 'Top Perdas', 'red');

    } catch (error) {
        console.error("Erro ao carregar dados:", error);
    }
}

function renderizarGraficoBarras(canvasId, labels, dataValues, label, color = '#36a2eb') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return; // Se o canvas não existir, ignora

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: dataValues,
                backgroundColor: color,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}