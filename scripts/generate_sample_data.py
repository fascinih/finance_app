#!/usr/bin/env python3
"""
Finance App - Gerador de Dados Sintéticos
Gera transações financeiras realistas para testes e demonstração.
"""

import random
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import csv
import argparse
from typing import List, Dict, Any
import sys
import os

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Dados para geração de transações realistas
CATEGORIES = {
    "Alimentação": {
        "subcategories": ["Supermercado", "Restaurante", "Delivery", "Padaria", "Açougue"],
        "merchants": [
            "Supermercado Pão de Açúcar", "Extra Supermercado", "Carrefour", "Big Bompreço",
            "Restaurante Outback", "McDonald's", "Burger King", "Subway", "iFood",
            "Padaria Central", "Padaria do Bairro", "Açougue São João"
        ],
        "amount_range": (15.0, 200.0),
        "frequency": 0.25  # 25% das transações
    },
    "Transporte": {
        "subcategories": ["Combustível", "Uber/99", "Transporte Público", "Estacionamento"],
        "merchants": [
            "Posto Shell", "Posto Ipiranga", "Posto BR", "Uber", "99 Táxi",
            "Metrô SP", "CPTM", "Estapar", "Zona Azul"
        ],
        "amount_range": (5.0, 120.0),
        "frequency": 0.15
    },
    "Moradia": {
        "subcategories": ["Aluguel", "Condomínio", "Energia", "Água", "Gás", "Internet"],
        "merchants": [
            "Imobiliária Central", "Administradora XYZ", "Enel Distribuição",
            "Sabesp", "Comgás", "Vivo Fibra", "NET Claro"
        ],
        "amount_range": (80.0, 1500.0),
        "frequency": 0.12
    },
    "Saúde": {
        "subcategories": ["Plano de Saúde", "Medicamentos", "Consultas", "Exames"],
        "merchants": [
            "Unimed", "Amil", "SulAmérica", "Farmácia São Paulo",
            "Drogasil", "Clínica São Camilo", "Hospital Albert Einstein"
        ],
        "amount_range": (25.0, 800.0),
        "frequency": 0.08
    },
    "Lazer": {
        "subcategories": ["Cinema", "Streaming", "Viagens", "Esportes", "Livros"],
        "merchants": [
            "Cinemark", "Netflix", "Spotify", "Amazon Prime", "Booking.com",
            "Decathlon", "Livraria Cultura", "Saraiva"
        ],
        "amount_range": (10.0, 500.0),
        "frequency": 0.10
    },
    "Vestuário": {
        "subcategories": ["Roupas", "Calçados", "Acessórios"],
        "merchants": [
            "C&A", "Renner", "Zara", "Nike", "Adidas", "Havaianas",
            "Shopping Center Norte", "Riachuelo"
        ],
        "amount_range": (30.0, 300.0),
        "frequency": 0.06
    },
    "Tecnologia": {
        "subcategories": ["Celular", "Internet", "Software", "Eletrônicos"],
        "merchants": [
            "Vivo", "Tim", "Claro", "Microsoft", "Apple", "Google Play",
            "Magazine Luiza", "Americanas", "Mercado Livre"
        ],
        "amount_range": (20.0, 1000.0),
        "frequency": 0.05
    },
    "Educação": {
        "subcategories": ["Cursos", "Livros", "Material Escolar"],
        "merchants": [
            "Udemy", "Coursera", "Alura", "Universidade Anhembi",
            "Kalunga", "Papelaria Central"
        ],
        "amount_range": (25.0, 400.0),
        "frequency": 0.04
    },
    "Bancos e Taxas": {
        "subcategories": ["Tarifas", "Juros", "Anuidade", "IOF"],
        "merchants": [
            "Banco do Brasil", "Itaú", "Bradesco", "Santander",
            "Nubank", "Inter", "C6 Bank"
        ],
        "amount_range": (5.0, 100.0),
        "frequency": 0.03
    }
}

INCOME_SOURCES = {
    "Salário": {
        "merchants": [
            "Empresa ABC Ltda", "Corporação XYZ", "Startup Tech",
            "Consultoria Financeira", "Agência Digital"
        ],
        "amount_range": (2500.0, 8000.0),
        "frequency": 0.60  # 60% das receitas
    },
    "Freelance": {
        "merchants": [
            "Cliente Freelance", "Projeto Consultoria", "Trabalho Extra",
            "Serviços Digitais"
        ],
        "amount_range": (300.0, 2000.0),
        "frequency": 0.20
    },
    "Investimentos": {
        "merchants": [
            "Tesouro Direto", "Banco Inter Investimentos", "XP Investimentos",
            "Rico Investimentos", "Dividendos Ações"
        ],
        "amount_range": (50.0, 1000.0),
        "frequency": 0.15
    },
    "Outros": {
        "merchants": [
            "Venda Produto", "Reembolso", "Cashback", "Prêmio"
        ],
        "amount_range": (20.0, 500.0),
        "frequency": 0.05
    }
}

LOCATIONS = [
    "São Paulo, SP", "Rio de Janeiro, RJ", "Belo Horizonte, MG",
    "Brasília, DF", "Salvador, BA", "Fortaleza, CE", "Recife, PE",
    "Porto Alegre, RS", "Curitiba, PR", "Campinas, SP"
]

TRANSACTION_TYPES = ["debit", "credit", "pix", "transfer"]


class SyntheticDataGenerator:
    """Gerador de dados sintéticos para transações financeiras."""
    
    def __init__(self, start_date: date = None, end_date: date = None):
        self.start_date = start_date or (date.today() - timedelta(days=365))
        self.end_date = end_date or date.today()
        self.transactions = []
        
    def generate_transactions(self, num_transactions: int = 1000) -> List[Dict[str, Any]]:
        """Gera lista de transações sintéticas."""
        
        print(f"Gerando {num_transactions} transações entre {self.start_date} e {self.end_date}")
        
        # Calcular proporção de receitas vs despesas (80% despesas, 20% receitas)
        num_expenses = int(num_transactions * 0.8)
        num_income = num_transactions - num_expenses
        
        # Gerar despesas
        for _ in range(num_expenses):
            transaction = self._generate_expense()
            self.transactions.append(transaction)
        
        # Gerar receitas
        for _ in range(num_income):
            transaction = self._generate_income()
            self.transactions.append(transaction)
        
        # Ordenar por data
        self.transactions.sort(key=lambda x: x['date'])
        
        # Adicionar padrões recorrentes
        self._add_recurring_patterns()
        
        return self.transactions
    
    def _generate_expense(self) -> Dict[str, Any]:
        """Gera uma transação de despesa."""
        
        # Escolher categoria baseada na frequência
        category_name = self._weighted_choice(CATEGORIES)
        category_data = CATEGORIES[category_name]
        
        # Gerar valores
        amount = -round(random.uniform(*category_data["amount_range"]), 2)
        merchant = random.choice(category_data["merchants"])
        subcategory = random.choice(category_data["subcategories"])
        
        # Gerar data aleatória
        transaction_date = self._random_date()
        
        # Tipo de transação
        tx_type = random.choice(["debit", "pix", "credit"])
        
        return {
            "id": str(uuid.uuid4()),
            "date": transaction_date.isoformat(),
            "datetime": datetime.combine(transaction_date, self._random_time()).isoformat(),
            "amount": amount,
            "description": self._generate_description(merchant, subcategory),
            "transaction_type": tx_type,
            "status": "completed",
            "account_id": f"acc_{random.randint(1000, 9999)}",
            "account_name": "Conta Corrente Principal",
            "counterpart_name": merchant,
            "counterpart_document": self._generate_document(),
            "location": random.choice(LOCATIONS),
            "channel": random.choice(["app", "website", "physical", "atm"]),
            "category": category_name,
            "subcategory": subcategory,
            "tags": self._generate_tags(category_name, subcategory),
            "notes": self._generate_notes()
        }
    
    def _generate_income(self) -> Dict[str, Any]:
        """Gera uma transação de receita."""
        
        # Escolher fonte de receita
        source_name = self._weighted_choice(INCOME_SOURCES)
        source_data = INCOME_SOURCES[source_name]
        
        # Gerar valores
        amount = round(random.uniform(*source_data["amount_range"]), 2)
        merchant = random.choice(source_data["merchants"])
        
        # Gerar data aleatória
        transaction_date = self._random_date()
        
        return {
            "id": str(uuid.uuid4()),
            "date": transaction_date.isoformat(),
            "datetime": datetime.combine(transaction_date, self._random_time()).isoformat(),
            "amount": amount,
            "description": self._generate_income_description(merchant, source_name),
            "transaction_type": "credit",
            "status": "completed",
            "account_id": f"acc_{random.randint(1000, 9999)}",
            "account_name": "Conta Corrente Principal",
            "counterpart_name": merchant,
            "counterpart_document": self._generate_document(),
            "location": random.choice(LOCATIONS),
            "channel": random.choice(["transfer", "deposit", "pix"]),
            "category": source_name,
            "subcategory": None,
            "tags": [source_name.lower(), "receita"],
            "notes": None
        }
    
    def _weighted_choice(self, choices_dict: Dict) -> str:
        """Escolha ponderada baseada na frequência."""
        
        choices = list(choices_dict.keys())
        weights = [choices_dict[choice]["frequency"] for choice in choices]
        
        return random.choices(choices, weights=weights)[0]
    
    def _random_date(self) -> date:
        """Gera data aleatória no período especificado."""
        
        delta = self.end_date - self.start_date
        random_days = random.randint(0, delta.days)
        
        return self.start_date + timedelta(days=random_days)
    
    def _random_time(self) -> datetime.time:
        """Gera horário aleatório."""
        
        hour = random.randint(6, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        
        return datetime.time(datetime(2024, 1, 1, hour, minute, second))
    
    def _generate_description(self, merchant: str, subcategory: str) -> str:
        """Gera descrição realista da transação."""
        
        templates = [
            f"{merchant}",
            f"{merchant} - {subcategory}",
            f"Compra {merchant}",
            f"Pagamento {merchant}",
            f"{subcategory} - {merchant}"
        ]
        
        return random.choice(templates)
    
    def _generate_income_description(self, merchant: str, source: str) -> str:
        """Gera descrição para receitas."""
        
        if source == "Salário":
            return f"Salário {merchant}"
        elif source == "Freelance":
            return f"Freelance - {merchant}"
        elif source == "Investimentos":
            return f"Rendimento {merchant}"
        else:
            return f"Receita - {merchant}"
    
    def _generate_document(self) -> str:
        """Gera documento (CNPJ) fictício."""
        
        return f"{random.randint(10, 99)}.{random.randint(100, 999)}.{random.randint(100, 999)}/0001-{random.randint(10, 99)}"
    
    def _generate_tags(self, category: str, subcategory: str) -> List[str]:
        """Gera tags para a transação."""
        
        tags = [category.lower(), subcategory.lower()]
        
        # Adicionar tags extras ocasionalmente
        if random.random() < 0.3:
            extra_tags = ["essencial", "lazer", "urgente", "planejado", "imprevisto"]
            tags.append(random.choice(extra_tags))
        
        return tags
    
    def _generate_notes(self) -> str:
        """Gera notas ocasionais."""
        
        if random.random() < 0.1:  # 10% das transações têm notas
            notes = [
                "Compra planejada",
                "Gasto imprevisto",
                "Promoção especial",
                "Necessidade urgente",
                "Investimento futuro"
            ]
            return random.choice(notes)
        
        return None
    
    def _add_recurring_patterns(self):
        """Adiciona padrões recorrentes realistas."""
        
        # Salário mensal
        current_date = self.start_date
        while current_date <= self.end_date:
            # Salário no 5º dia útil do mês
            salary_date = current_date.replace(day=5)
            if salary_date <= self.end_date:
                salary_transaction = {
                    "id": str(uuid.uuid4()),
                    "date": salary_date.isoformat(),
                    "datetime": datetime.combine(salary_date, datetime.time(datetime(2024, 1, 1, 9, 0, 0))).isoformat(),
                    "amount": round(random.uniform(4000, 6000), 2),
                    "description": "Salário Mensal - Empresa ABC",
                    "transaction_type": "credit",
                    "status": "completed",
                    "account_id": "acc_1001",
                    "account_name": "Conta Corrente Principal",
                    "counterpart_name": "Empresa ABC Ltda",
                    "counterpart_document": "12.345.678/0001-90",
                    "location": "São Paulo, SP",
                    "channel": "transfer",
                    "category": "Salário",
                    "subcategory": None,
                    "tags": ["salario", "mensal", "receita"],
                    "notes": "Pagamento mensal"
                }
                self.transactions.append(salary_transaction)
            
            # Próximo mês
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        # Netflix mensal
        current_date = self.start_date
        while current_date <= self.end_date:
            netflix_date = current_date.replace(day=15)
            if netflix_date <= self.end_date:
                netflix_transaction = {
                    "id": str(uuid.uuid4()),
                    "date": netflix_date.isoformat(),
                    "datetime": datetime.combine(netflix_date, datetime.time(datetime(2024, 1, 1, 20, 30, 0))).isoformat(),
                    "amount": -39.90,
                    "description": "Netflix Assinatura Mensal",
                    "transaction_type": "debit",
                    "status": "completed",
                    "account_id": "acc_1001",
                    "account_name": "Conta Corrente Principal",
                    "counterpart_name": "Netflix",
                    "counterpart_document": "13.456.789/0001-12",
                    "location": "Online",
                    "channel": "app",
                    "category": "Lazer",
                    "subcategory": "Streaming",
                    "tags": ["netflix", "streaming", "mensal"],
                    "notes": "Assinatura recorrente"
                }
                self.transactions.append(netflix_transaction)
            
            # Próximo mês
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
    
    def save_to_csv(self, filename: str):
        """Salva transações em arquivo CSV."""
        
        print(f"Salvando {len(self.transactions)} transações em {filename}")
        
        fieldnames = [
            "id", "date", "datetime", "amount", "description", "transaction_type",
            "status", "account_id", "account_name", "counterpart_name",
            "counterpart_document", "location", "channel", "category",
            "subcategory", "tags", "notes"
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for transaction in self.transactions:
                # Converter tags para string
                row = transaction.copy()
                if row['tags']:
                    row['tags'] = ','.join(row['tags'])
                
                writer.writerow(row)
    
    def save_to_json(self, filename: str):
        """Salva transações em arquivo JSON."""
        
        print(f"Salvando {len(self.transactions)} transações em {filename}")
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.transactions, jsonfile, indent=2, ensure_ascii=False)
    
    def print_summary(self):
        """Imprime resumo das transações geradas."""
        
        total_transactions = len(self.transactions)
        total_income = sum(tx['amount'] for tx in self.transactions if tx['amount'] > 0)
        total_expenses = sum(abs(tx['amount']) for tx in self.transactions if tx['amount'] < 0)
        net_amount = total_income - total_expenses
        
        print(f"\n=== Resumo das Transações Geradas ===")
        print(f"Total de transações: {total_transactions}")
        print(f"Receitas: R$ {total_income:,.2f}")
        print(f"Despesas: R$ {total_expenses:,.2f}")
        print(f"Saldo líquido: R$ {net_amount:,.2f}")
        
        # Resumo por categoria
        categories_summary = {}
        for tx in self.transactions:
            category = tx['category']
            if category not in categories_summary:
                categories_summary[category] = {'count': 0, 'amount': 0}
            
            categories_summary[category]['count'] += 1
            categories_summary[category]['amount'] += abs(tx['amount'])
        
        print(f"\n=== Resumo por Categoria ===")
        for category, data in sorted(categories_summary.items(), key=lambda x: x[1]['amount'], reverse=True):
            print(f"{category}: {data['count']} transações, R$ {data['amount']:,.2f}")


def main():
    """Função principal."""
    
    parser = argparse.ArgumentParser(description="Gerador de dados sintéticos para Finance App")
    parser.add_argument("--transactions", "-t", type=int, default=1000, help="Número de transações a gerar")
    parser.add_argument("--days", "-d", type=int, default=365, help="Número de dias no passado")
    parser.add_argument("--output", "-o", default="sample_transactions", help="Nome base dos arquivos de saída")
    parser.add_argument("--format", "-f", choices=["csv", "json", "both"], default="both", help="Formato de saída")
    
    args = parser.parse_args()
    
    # Calcular datas
    end_date = date.today()
    start_date = end_date - timedelta(days=args.days)
    
    # Gerar dados
    generator = SyntheticDataGenerator(start_date, end_date)
    transactions = generator.generate_transactions(args.transactions)
    
    # Salvar arquivos
    if args.format in ["csv", "both"]:
        generator.save_to_csv(f"{args.output}.csv")
    
    if args.format in ["json", "both"]:
        generator.save_to_json(f"{args.output}.json")
    
    # Mostrar resumo
    generator.print_summary()
    
    print(f"\n✅ Dados sintéticos gerados com sucesso!")
    print(f"Arquivos salvos: {args.output}.csv e/ou {args.output}.json")


if __name__ == "__main__":
    main()

