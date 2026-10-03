class AntiFraudEngine:
    @staticmethod
    def is_valid_request(client_ip: str, user_agent: str) -> bool:
        """
        Valida se a requisição de anúncio vem de um usuário humano válido.
        """
        if not user_agent or "bot" in user_agent.lower() or "crawl" in user_agent.lower():
            return False

        # Filtro básico de IP reservado/localhost
        if client_ip in ["127.0.0.1", "localhost"]:
            return True  # Permitido para testes locais

        return True
