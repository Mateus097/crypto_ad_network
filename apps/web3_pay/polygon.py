import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# ABI Mínimo para interagir com contratos ERC-20 / BEP-20 (Função transfer e decimals)
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

# Endereço do contrato USDT na rede Polygon Mainnet
USDT_POLYGON_ADDRESS = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"


class PolygonPayoutEngine:
    def __init__(self):
        self.rpc_url = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.private_key = os.getenv("PLATFORM_PRIVATE_KEY")
        self.sender_address = os.getenv("PLATFORM_WALLET_ADDRESS")

    def send_usdt(self, to_address: str, amount_usd: float) -> str:
        """
        Envia USDT via Polygon Mainnet para a carteira do publisher.
        Retorna o Hash da Transação em caso de sucesso.
        """
        if not self.w3.is_connected():
            raise Exception("Falha ao conectar ao nó da Polygon RPC")

        account = self.w3.eth.account.from_key(self.private_key)
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(USDT_POLYGON_ADDRESS),
            abi=ERC20_ABI
        )

        # USDT na Polygon utiliza 6 casas decimais
        decimals = 6
        amount_in_units = int(amount_usd * (10 ** decimals))

        # Obter a taxa de gas (EIP-1559) e o nonce da transação
        nonce = self.w3.eth.get_transaction_count(self.sender_address)

        tx = contract.functions.transfer(
            Web3.to_checksum_address(to_address),
            amount_in_units
        ).build_transaction({
            'chainId': 137,  # Polygon Mainnet
            'gas': 100000,
            'maxFeePerGas': self.w3.eth.gas_price * 2,
            'maxPriorityFeePerGas': self.w3.to_wei('30', 'gwei'),
            'nonce': nonce,
        })

        # Assinar e transmitir a transação para a rede
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        return self.w3.to_hex(tx_hash)