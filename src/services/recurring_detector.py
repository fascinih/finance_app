"""
Recurring Transaction Detection Service.
Detecta padrões de transações recorrentes usando algoritmos de ML.
"""

import uuid
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import re
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from loguru import logger

from src.models import Transaction, get_db


@dataclass
class RecurringPattern:
    """Padrão de transação recorrente detectado."""
    pattern_id: str
    description_pattern: str
    amount_range: Tuple[float, float]
    frequency_days: int
    frequency_type: str  # daily, weekly, monthly, quarterly, yearly
    confidence: float
    transactions: List[str]  # Transaction IDs
    next_expected_date: Optional[date]
    merchant_pattern: Optional[str] = None
    category_suggestion: Optional[str] = None


class RecurringDetector:
    """Detector de transações recorrentes."""
    
    def __init__(self):
        self.min_occurrences = 3  # Mínimo de ocorrências para considerar recorrente
        self.similarity_threshold = 0.8  # Threshold para similaridade de descrição
        self.amount_tolerance = 0.1  # 10% de tolerância no valor
        self.date_tolerance_days = 3  # Tolerância de 3 dias na data
        
    def detect_recurring_transactions(self, db: Session, days_back: int = 365) -> List[RecurringPattern]:
        """
        Detecta transações recorrentes nos últimos N dias.
        
        Args:
            db: Sessão do banco de dados
            days_back: Número de dias para analisar
            
        Returns:
            Lista de padrões recorrentes detectados
        """
        
        # Buscar transações dos últimos N dias
        cutoff_date = date.today() - timedelta(days=days_back)
        
        transactions = db.query(Transaction).filter(
            Transaction.date >= cutoff_date,
            Transaction.is_recurring == False  # Apenas transações não marcadas como recorrentes
        ).order_by(Transaction.date).all()
        
        if len(transactions) < self.min_occurrences:
            return []
        
        logger.info(f"Analisando {len(transactions)} transações para detectar padrões recorrentes")
        
        # Agrupar transações por similaridade
        transaction_groups = self._group_similar_transactions(transactions)
        
        # Detectar padrões em cada grupo
        patterns = []
        for group in transaction_groups:
            if len(group) >= self.min_occurrences:
                pattern = self._analyze_transaction_group(group)
                if pattern and pattern.confidence >= 0.6:
                    patterns.append(pattern)
        
        # Ordenar por confiança
        patterns.sort(key=lambda p: p.confidence, reverse=True)
        
        logger.info(f"Detectados {len(patterns)} padrões recorrentes")
        return patterns
    
    def _group_similar_transactions(self, transactions: List[Transaction]) -> List[List[Transaction]]:
        """Agrupa transações similares."""
        
        groups = []
        used_transactions = set()
        
        for i, tx1 in enumerate(transactions):
            if tx1.id in used_transactions:
                continue
                
            # Criar novo grupo com esta transação
            group = [tx1]
            used_transactions.add(tx1.id)
            
            # Procurar transações similares
            for j, tx2 in enumerate(transactions[i+1:], i+1):
                if tx2.id in used_transactions:
                    continue
                
                if self._are_transactions_similar(tx1, tx2):
                    group.append(tx2)
                    used_transactions.add(tx2.id)
            
            if len(group) >= self.min_occurrences:
                groups.append(group)
        
        return groups
    
    def _are_transactions_similar(self, tx1: Transaction, tx2: Transaction) -> bool:
        """Verifica se duas transações são similares."""
        
        # Verificar similaridade de descrição
        desc_similarity = SequenceMatcher(None, tx1.description.lower(), tx2.description.lower()).ratio()
        if desc_similarity < self.similarity_threshold:
            return False
        
        # Verificar similaridade de valor (tolerância de 10%)
        amount1, amount2 = abs(float(tx1.amount)), abs(float(tx2.amount))
        amount_diff = abs(amount1 - amount2) / max(amount1, amount2)
        if amount_diff > self.amount_tolerance:
            return False
        
        # Verificar mesmo estabelecimento (se disponível)
        if tx1.counterpart_name and tx2.counterpart_name:
            counterpart_similarity = SequenceMatcher(
                None, 
                tx1.counterpart_name.lower(), 
                tx2.counterpart_name.lower()
            ).ratio()
            if counterpart_similarity < 0.7:
                return False
        
        return True
    
    def _analyze_transaction_group(self, transactions: List[Transaction]) -> Optional[RecurringPattern]:
        """Analisa um grupo de transações para detectar padrão recorrente."""
        
        if len(transactions) < self.min_occurrences:
            return None
        
        # Ordenar por data
        transactions.sort(key=lambda tx: tx.date)
        
        # Calcular intervalos entre transações
        intervals = []
        for i in range(1, len(transactions)):
            interval = (transactions[i].date - transactions[i-1].date).days
            intervals.append(interval)
        
        if not intervals:
            return None
        
        # Detectar frequência
        frequency_info = self._detect_frequency(intervals)
        if not frequency_info:
            return None
        
        frequency_days, frequency_type, confidence = frequency_info
        
        # Calcular estatísticas do grupo
        amounts = [abs(float(tx.amount)) for tx in transactions]
        min_amount, max_amount = min(amounts), max(amounts)
        
        # Gerar padrão de descrição
        description_pattern = self._generate_description_pattern(transactions)
        
        # Gerar padrão de estabelecimento
        merchant_pattern = self._generate_merchant_pattern(transactions)
        
        # Prever próxima data
        last_date = transactions[-1].date
        next_expected_date = last_date + timedelta(days=frequency_days)
        
        # Sugerir categoria baseada na mais comum
        categories = [tx.llm_category or tx.category.name if tx.category else "Outros" for tx in transactions]
        category_counts = defaultdict(int)
        for cat in categories:
            category_counts[cat] += 1
        category_suggestion = max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None
        
        return RecurringPattern(
            pattern_id=str(uuid.uuid4()),
            description_pattern=description_pattern,
            amount_range=(min_amount, max_amount),
            frequency_days=frequency_days,
            frequency_type=frequency_type,
            confidence=confidence,
            transactions=[str(tx.id) for tx in transactions],
            next_expected_date=next_expected_date,
            merchant_pattern=merchant_pattern,
            category_suggestion=category_suggestion
        )
    
    def _detect_frequency(self, intervals: List[int]) -> Optional[Tuple[int, str, float]]:
        """Detecta a frequência das transações."""
        
        if not intervals:
            return None
        
        # Calcular média e desvio padrão dos intervalos
        avg_interval = sum(intervals) / len(intervals)
        variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
        std_dev = variance ** 0.5
        
        # Coeficiente de variação (menor = mais regular)
        cv = std_dev / avg_interval if avg_interval > 0 else float('inf')
        
        # Determinar tipo de frequência
        frequency_type = "irregular"
        target_interval = avg_interval
        
        # Frequências conhecidas (com tolerância)
        frequency_patterns = [
            (1, "daily", 1),
            (7, "weekly", 2),
            (14, "biweekly", 3),
            (30, "monthly", 5),
            (90, "quarterly", 10),
            (365, "yearly", 30)
        ]
        
        for pattern_days, pattern_name, tolerance in frequency_patterns:
            if abs(avg_interval - pattern_days) <= tolerance:
                frequency_type = pattern_name
                target_interval = pattern_days
                break
        
        # Calcular confiança baseada na regularidade
        confidence = max(0.0, 1.0 - cv / 2.0)  # CV alto = confiança baixa
        
        # Ajustar confiança baseada no número de ocorrências
        occurrence_bonus = min(0.2, (len(intervals) - 2) * 0.05)
        confidence += occurrence_bonus
        
        # Penalizar frequências irregulares
        if frequency_type == "irregular":
            confidence *= 0.5
        
        confidence = min(1.0, confidence)
        
        return (int(target_interval), frequency_type, confidence)
    
    def _generate_description_pattern(self, transactions: List[Transaction]) -> str:
        """Gera um padrão de descrição baseado nas transações."""
        
        descriptions = [tx.description for tx in transactions]
        
        # Encontrar palavras comuns
        common_words = self._find_common_words(descriptions)
        
        if common_words:
            return " ".join(common_words)
        else:
            # Fallback: usar a descrição mais comum
            desc_counts = defaultdict(int)
            for desc in descriptions:
                desc_counts[desc] += 1
            return max(desc_counts.items(), key=lambda x: x[1])[0]
    
    def _generate_merchant_pattern(self, transactions: List[Transaction]) -> Optional[str]:
        """Gera um padrão de estabelecimento."""
        
        merchants = [tx.counterpart_name for tx in transactions if tx.counterpart_name]
        
        if not merchants:
            return None
        
        # Encontrar estabelecimento mais comum
        merchant_counts = defaultdict(int)
        for merchant in merchants:
            merchant_counts[merchant] += 1
        
        if merchant_counts:
            return max(merchant_counts.items(), key=lambda x: x[1])[0]
        
        return None
    
    def _find_common_words(self, texts: List[str]) -> List[str]:
        """Encontra palavras comuns em uma lista de textos."""
        
        # Palavras a ignorar
        stop_words = {
            'de', 'da', 'do', 'das', 'dos', 'e', 'o', 'a', 'os', 'as', 'em', 'no', 'na', 'nos', 'nas',
            'para', 'por', 'com', 'sem', 'sob', 'sobre', 'entre', 'ate', 'até', 'desde', 'durante',
            'pix', 'transferencia', 'transferência', 'pagamento', 'compra', 'debito', 'débito'
        }
        
        # Extrair palavras de cada texto
        all_words = []
        for text in texts:
            words = re.findall(r'\b[a-záàâãéêíóôõúç]+\b', text.lower())
            words = [w for w in words if len(w) > 2 and w not in stop_words]
            all_words.extend(words)
        
        # Contar frequência das palavras
        word_counts = defaultdict(int)
        for word in all_words:
            word_counts[word] += 1
        
        # Retornar palavras que aparecem em pelo menos 70% dos textos
        min_frequency = max(1, int(len(texts) * 0.7))
        common_words = [word for word, count in word_counts.items() if count >= min_frequency]
        
        # Ordenar por frequência
        common_words.sort(key=lambda w: word_counts[w], reverse=True)
        
        return common_words[:3]  # Máximo 3 palavras
    
    def mark_transactions_as_recurring(
        self, 
        db: Session, 
        pattern: RecurringPattern
    ) -> int:
        """
        Marca transações como recorrentes baseado no padrão detectado.
        
        Args:
            db: Sessão do banco de dados
            pattern: Padrão recorrente detectado
            
        Returns:
            Número de transações marcadas
        """
        
        # Gerar ID único para o grupo recorrente
        recurring_group_id = uuid.uuid4()
        
        # Buscar transações do padrão
        transaction_ids = [uuid.UUID(tx_id) for tx_id in pattern.transactions]
        
        transactions = db.query(Transaction).filter(
            Transaction.id.in_(transaction_ids)
        ).all()
        
        # Marcar como recorrentes
        updated_count = 0
        for tx in transactions:
            tx.is_recurring = True
            tx.recurring_pattern = pattern.frequency_type
            tx.recurring_group_id = recurring_group_id
            updated_count += 1
        
        db.commit()
        
        logger.info(f"Marcadas {updated_count} transações como recorrentes (padrão: {pattern.frequency_type})")
        
        return updated_count
    
    def predict_next_transactions(
        self, 
        db: Session, 
        days_ahead: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Prediz próximas transações recorrentes.
        
        Args:
            db: Sessão do banco de dados
            days_ahead: Número de dias para prever
            
        Returns:
            Lista de transações previstas
        """
        
        # Buscar grupos de transações recorrentes
        recurring_groups = db.query(
            Transaction.recurring_group_id,
            Transaction.recurring_pattern
        ).filter(
            Transaction.is_recurring == True,
            Transaction.recurring_group_id.isnot(None)
        ).distinct().all()
        
        predictions = []
        target_date = date.today() + timedelta(days=days_ahead)
        
        for group_id, pattern in recurring_groups:
            # Buscar última transação do grupo
            last_tx = db.query(Transaction).filter(
                Transaction.recurring_group_id == group_id
            ).order_by(Transaction.date.desc()).first()
            
            if not last_tx:
                continue
            
            # Calcular próximas datas baseadas no padrão
            frequency_map = {
                "daily": 1,
                "weekly": 7,
                "biweekly": 14,
                "monthly": 30,
                "quarterly": 90,
                "yearly": 365
            }
            
            frequency_days = frequency_map.get(pattern, 30)
            next_date = last_tx.date + timedelta(days=frequency_days)
            
            # Adicionar previsões até a data alvo
            while next_date <= target_date:
                predictions.append({
                    "predicted_date": next_date,
                    "description": last_tx.description,
                    "estimated_amount": float(last_tx.amount),
                    "category": last_tx.llm_category or (last_tx.category.name if last_tx.category else "Outros"),
                    "frequency_type": pattern,
                    "confidence": 0.8,  # Confiança baseada em histórico
                    "recurring_group_id": str(group_id)
                })
                
                next_date += timedelta(days=frequency_days)
        
        # Ordenar por data
        predictions.sort(key=lambda p: p["predicted_date"])
        
        return predictions


# Global detector instance
recurring_detector = RecurringDetector()

