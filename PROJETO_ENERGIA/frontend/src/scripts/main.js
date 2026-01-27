// ---------- left Sidebar js -------------------

$(document).on('click', '#sidebar li', function () {
    $(this).addClass('active').siblings().removeClass('active')
});

$('.sub-menu ul').hide();
$(".sub-menu a").click(function () {
    $(this).parent(".sub-menu").children("ul").slideToggle("100");
    $(this).find(".right").toggleClass("fa-caret-up fa-caret-down");
});

// ---------------- Sidebar toggle ----------------

$(document).ready(function () {
    $("#toggleSidebar").click(function () {
        $(".left-menu").toggleClass("hide");
        $(".content-wrapper").toggleClass("hide");
    });
});

// ----------------  Table ----------------

$(document).ready(function () {
    if ($('#table-p3').length) {
        $('#table-p3').DataTable();
    }
});

// ---------------- Dashboard Logic ----------------

document.addEventListener("DOMContentLoaded", function () {
    carregarDadosDashboard();
});

async function carregarDadosDashboard() {
    try {
        console.log("Iniciando carregamento do dashboard...");
        
        // Chama a API criada em Python
        const response = await fetch('/api/dashboard/resumo');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Dados recebidos:", data);

        if (data.cards) {
            // Função formatadora de moeda BRL
            const fmt = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

            // Atualiza os Cards (Texto)
            const cardCusto = document.getElementById('card-custo-mensal');
            const cardPerda = document.getElementById('card-perda-mensal');

            if (cardCusto) cardCusto.innerText = fmt.format(data.cards.custo_mensal);
            if (cardPerda) cardPerda.innerText = fmt.format(data.cards.perda_mensal);
        }

        // Renderiza o Gráfico de Custo por Loja
        if (data.grafico_custo_loja) {
             // Reutilizando lógica genérica ou chamando função específica
             renderizarGraficoBarras(
                 'CTotalLoja', // ID do canvas (ajuste conforme seu HTML)
                 data.grafico_custo_loja.labels, 
                 data.grafico_custo_loja.values, 
                 'Custo Total (R$)',
                 'rgba(54, 162, 235, 0.7)'
             );
        }

        // Renderiza o Gráfico de Top Perdas
        if (data.grafico_top_perdas) {
            renderizarGraficoBarras(
                'chartDezMaisPerdas', // ID do canvas (ajuste conforme seu HTML)
                data.grafico_top_perdas.labels, 
                data.grafico_top_perdas.values, 
                'Top Perdas (R$)', 
                'rgba(255, 99, 132, 0.7)' // Vermelho
            );
        }

        // Exemplo: Se houver um gráfico de "Custo Mensal" geral (adaptado do código antigo)
        // Aqui você pode criar chamadas adicionais se a API retornar dados históricos
        
    } catch (error) {
        console.error("Erro ao carregar dados do dashboard:", error);
    }
}

/**
 * Função genérica para renderizar gráficos de barra usando Chart.js
 */
function renderizarGraficoBarras(canvasId, labels, dataValues, label, color) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.warn(`Canvas com id '${canvasId}' não encontrado.`);
        return;
    }

    // Destrói gráfico anterior se existir para evitar sobreposição ao recarregar
    if (window[canvasId] instanceof Chart) {
        window[canvasId].destroy();
    }

    window[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: dataValues,
                backgroundColor: color,
                borderColor: color.replace('0.7', '1'), // Borda um pouco mais forte
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y', // Mantendo o padrão horizontal visto no código antigo
            scales: {
                x: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}