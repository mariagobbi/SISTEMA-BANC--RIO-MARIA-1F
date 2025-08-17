from getpass import getpass
from typing import List, Dict, Optional
from datetime import datetime

# DADOS EM MEMÓRIA 
contas: List[Dict] = []  # cada conta: {'numero': int, 'nome': str, 'senha': str, 'saldo': float, 'ativa': bool}

# Matriz de taxas: [taxa_fixa, taxa_percentual]
# índice 0 = depósito, 1 = saque, 2 = transferência
taxas_matriz: List[List[float]] = [
    [0.50, 0.00],  # depósito: R$0,50
    [1.00, 0.01],  # saque:    R$1,00 + 1% do valor
    [2.00, 0.02],  # transf.:  R$2,00 + 2% do valor
]

# Matriz de transações para auditoria/relatório
# [timestamp, tipo, origem_num, destino_num, valor, taxa, saldo_origem_pos, saldo_destino_pos]
transacoes: List[List] = []

GERENTE_SENHA = "gerente123"  # para listar saldos globais


# ---------------------- FUNÇÕES DE APOIO ----------------------
def encontrar_conta_por_numero(numero: int) -> Optional[Dict]:
    for c in contas:
        if c['numero'] == numero and c['ativa']:
            return c
    return None


def calcular_taxa(indice_servico: int, valor: float) -> float:
    fixa, perc = taxas_matriz[indice_servico]
    return fixa + (perc * valor)


def ler_float_positivo(msg: str) -> float:
    while True:
        try:
            v = float(input(msg).replace(',', '.'))
            if v <= 0:
                print("Valor deve ser positivo.")
                continue
            return round(v, 2)
        except ValueError:
            print("Entrada inválida. Digite um número.")


def ler_int(msg: str) -> int:
    while True:
        try:
            return int(input(msg))
        except ValueError:
            print("Entrada inválida. Digite um número inteiro.")


# ---------------------- OPERAÇÕES PRINCIPAIS ----------------------
def cadastrar_conta() -> None:
    print("\n=== CADASTRO DE CONTA ===")
    numero = ler_int("Número da conta (inteiro, único): ")
    if encontrar_conta_por_numero(numero):
        print("Já existe uma conta com esse número.")
        return
    nome = input("Nome do titular: ").strip()
    senha = getpass("Crie uma senha: ")
    saldo_inicial = ler_float_positivo("Saldo inicial (R$): ")
    conta = {'numero': numero, 'nome': nome, 'senha': senha, 'saldo': round(saldo_inicial, 2), 'ativa': True}
    contas.append(conta)
    print(f"Conta criada com sucesso para {nome}. Número: {numero}. Saldo: R${conta['saldo']:.2f}")


def autenticar() -> Optional[Dict]:
    print("\n=== LOGIN ===")
    numero = ler_int("Número da conta: ")
    senha = getpass("Senha: ")
    conta = encontrar_conta_por_numero(numero)
    if not conta or conta['senha'] != senha:
        print("Credenciais inválidas.")
        return None
    print(f"Bem-vindo(a), {conta['nome']}!")
    return conta


def ver_saldo(conta: Dict) -> None:
    print(f"Saldo atual: R${conta['saldo']:.2f}")


def deposito(conta: Dict) -> None:
    print("\n=== DEPÓSITO ===")
    valor = ler_float_positivo("Valor do depósito (R$): ")
    taxa = calcular_taxa(0, valor)
    total = valor - taxa
    if total <= 0:
        print("Valor muito baixo frente à taxa. Operação cancelada.")
        return
    conta['saldo'] = round(conta['saldo'] + total, 2)
    transacoes.append([datetime.now().isoformat(timespec='seconds'), 'DEPÓSITO', conta['numero'], None, valor, taxa, conta['saldo'], None])
    print(f"Depósito de R${valor:.2f} realizado. Taxa: R${taxa:.2f}. Crédito líquido: R${total:.2f}.")
    ver_saldo(conta)


def saque(conta: Dict) -> None:
    print("\n=== SAQUE ===")
    valor = ler_float_positivo("Valor do saque (R$): ")
    taxa = calcular_taxa(1, valor)
    total = valor + taxa
    if conta['saldo'] < total:
        print(f"Saldo insuficiente. É necessário R${total:.2f} (inclui taxa de R${taxa:.2f}).")
        return
    conta['saldo'] = round(conta['saldo'] - total, 2)
    transacoes.append([datetime.now().isoformat(timespec='seconds'), 'SAQUE', conta['numero'], None, valor, taxa, conta['saldo'], None])
    print(f"Saque de R${valor:.2f} realizado. Taxa: R${taxa:.2f}. Débito total: R${total:.2f}.")
    ver_saldo(conta)


def transferencia(conta_origem: Dict) -> None:
    print("\n=== TRANSFERÊNCIA ===")
    destino_num = ler_int("Número da conta destino: ")
    conta_destino = encontrar_conta_por_numero(destino_num)
    if not conta_destino:
        print("Conta destino não encontrada/ativa.")
        return
    if conta_destino['numero'] == conta_origem['numero']:
        print("Não é permitido transferir para a mesma conta.")
        return
    valor = ler_float_positivo("Valor da transferência (R$): ")
    taxa = calcular_taxa(2, valor)
    total = valor + taxa
    if conta_origem['saldo'] < total:
        print(f"Saldo insuficiente. Necessário R${total:.2f} (inclui taxa de R${taxa:.2f}).")
        return
    conta_origem['saldo'] = round(conta_origem['saldo'] - total, 2)
    conta_destino['saldo'] = round(conta_destino['saldo'] + valor, 2)
    transacoes.append([datetime.now().isoformat(timespec='seconds'), 'TRANSFERÊNCIA', conta_origem['numero'], conta_destino['numero'], valor, taxa, conta_origem['saldo'], conta_destino['saldo']])
    print(f"Transferência de R${valor:.2f} para a conta {destino_num} realizada. Taxa: R${taxa:.2f}.")
    ver_saldo(conta_origem)


def listar_saldos_gerente() -> None:
    print("\n=== LISTAGEM DE SALDOS (GERENTE) ===")
    senha = getpass("Senha do gerente: ")
    if senha != GERENTE_SENHA:
        print("Senha incorreta.")
        return
    if not contas:
        print("Nenhuma conta cadastrada.")
        return
    print(f"{'Conta':>8} | {'Titular':<20} | {'Saldo (R$)':>12}")
    print("-" * 46)
    for c in contas:
        status = "" if c['ativa'] else "(inativa)"
        print(f"{c['numero']:>8} | {c['nome']:<20} | {c['saldo']:>12.2f} {status}")
    print("-" * 46)


def mostrar_taxas() -> None:
    print("\n=== TABELA DE TAXAS ===")
    print("Serviço         Taxa fixa   Percentual")
    print("---------------------------------------")
    nomes = ["Depósito", "Saque   ", "Transfer."]
    for i, nome in enumerate(nomes):
        fixa, perc = taxas_matriz[i]
        print(f"{nome:12}   R${fixa:>6.2f}    {perc*100:>6.2f}%")


def menu_conta(conta: Dict) -> None:
    while True:
        print("\n--- MENU DA CONTA ---")
        print("1) Ver saldo")
        print("2) Depósito")
        print("3) Saque")
        print("4) Transferência")
        print("5) Tabela de taxas")
        print("0) Sair da conta")
        op = input("Escolha: ").strip()
        if op == "1":
            ver_saldo(conta)
        elif op == "2":
            deposito(conta)
        elif op == "3":
            saque(conta)
        elif op == "4":
            transferencia(conta)
        elif op == "5":
            mostrar_taxas()
        elif op == "0":
            print("Logout efetuado.")
            break
        else:
            print("Opção inválida.")


def menu_principal() -> None:
    while True:
        print("\n=== SISTEMA BANCÁRIO ===")
        print("1) Cadastrar conta")
        print("2) Login")
        print("3) Listar saldos (gerente)")
        print("4) Mostrar taxas")
        print("0) Sair")
        op = input("Escolha: ").strip()
        if op == "1":
            cadastrar_conta()
        elif op == "2":
            conta = autenticar()
            if conta:
                menu_conta(conta)
        elif op == "3":
            listar_saldos_gerente()
        elif op == "4":
            mostrar_taxas()
        elif op == "0":
            print("Encerrando...")
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    menu_principal()
