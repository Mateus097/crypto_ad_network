(function () {
    // 1. Identifica a tag do script para capturar o ID do Publisher
    const currentScript = document.currentScript || Array.from(document.scripts).pop();
    const publisherId = currentScript.getAttribute('data-publisher') || currentScript.getAttribute('data-publisher-id') || '1';

    // URL da API local
    const API_URL = 'http://127.0.0.1:8000/api/v1/adserver/get-ad';

    // 2. Cria o container do anúncio de forma segura no DOM (sem usar document.write)
    const adContainer = document.createElement('div');
    adContainer.className = 'crypto-ad-container';
    adContainer.style.cssText = 'display: inline-block; width: 300px; height: 250px; border: 1px solid #30363d; border-radius: 8px; overflow: hidden; background-color: #0d1117; text-align: center; font-family: sans-serif;';

    // Insere o container logo após o script na página parceira
    currentScript.parentNode.insertBefore(adContainer, currentScript.nextSibling);

    // 3. Busca o anúncio na API FastAPI
    fetch(`${API_URL}?publisher_id=${publisherId}`)
        .then(response => {
            if (!response.ok) throw new Error('Erro na rede ao buscar anúncio');
            return response.json();
        })
        .then(data => {
            if (data.status === 'success' && data.ad) {
                adContainer.innerHTML = `
                    <a href="${data.ad.target_url}" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: block;">
                        <img src="${data.ad.image_url}" alt="Anúncio Web3" style="width: 100%; height: 220px; object-fit: cover; display: block;">
                        <div style="font-size: 10px; color: #8b949e; padding: 4px; background: #161b22; border-top: 1px solid #21262d;">
                            Anúncio Web3 • Patrocinado
                        </div>
                    </a>
                `;
            } else {
                adContainer.innerHTML = '<div style="color: #8b949e; line-height: 250px; font-size: 12px;">Sem anúncios disponíveis</div>';
            }
        })
        .catch(err => {
            console.error('CryptoAdNetwork:', err);
            adContainer.innerHTML = '<div style="color: #ff7b72; line-height: 250px; font-size: 12px;">Erro ao carregar anúncio</div>';
        });
})();
