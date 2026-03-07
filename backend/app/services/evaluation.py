"""
HR-RAG LLM Evaluation Module
Based on RAGAS and custom evaluation metrics
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import numpy as np
import asyncio
from datetime import datetime
import json

@dataclass
class EvaluationMetrics:
    """Metrics สำหรับประเมินผล RAG"""
    # Retrieval Metrics
    precision_at_k: float
    recall_at_k: float
    mrr: float  # Mean Reciprocal Rank
    ndcg: float  # Normalized DCG
    hit_rate: float
    
    # Generation Metrics
    faithfulness: float
    answer_relevance: float
    context_precision: float
    context_recall: float
    hallucination_rate: float
    
    # End-to-End Metrics
    accuracy: float
    response_time: float
    
    # Thai-specific Metrics
    thai_tokenization_score: float
    thai_semantic_similarity: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "precision_at_k": self.precision_at_k,
            "recall_at_k": self.recall_at_k,
            "mrr": self.mrr,
            "ndcg": self.ndcg,
            "hit_rate": self.hit_rate,
            "faithfulness": self.faithfulness,
            "answer_relevance": self.answer_relevance,
            "context_precision": self.context_precision,
            "context_recall": self.context_recall,
            "hallucination_rate": self.hallucination_rate,
            "accuracy": self.accuracy,
            "response_time": self.response_time,
            "thai_tokenization_score": self.thai_tokenization_score,
            "thai_semantic_similarity": self.thai_semantic_similarity,
        }
    
    def get_overall_score(self) -> float:
        """คำนวณคะแนนรวม"""
        weights = {
            "precision_at_k": 0.15,
            "recall_at_k": 0.15,
            "faithfulness": 0.20,
            "answer_relevance": 0.15,
            "accuracy": 0.15,
            "hallucination_rate": -0.20,  # Negative weight
        }
        
        score = 0
        for metric, weight in weights.items():
            value = getattr(self, metric)
            if metric == "hallucination_rate":
                score += (1 - value) * abs(weight)  # Lower is better
            else:
                score += value * weight
        
        return max(0, min(1, score))


@dataclass
class TestCase:
    """Test case สำหรับ evaluation"""
    id: str
    query: str
    query_type: str  # easy, complex, edge_case, out_of_scope, multi_hop
    expected_answer: str
    relevant_docs: List[str]
    expected_contexts: List[str]
    category: str  # hr_policy, legal, benefits, general


class RAGEvaluator:
    """Evaluator สำหรับ RAG System"""
    
    def __init__(self, llm_client, embedding_service, vector_store):
        self.llm = llm_client
        self.embeddings = embedding_service
        self.vector_store = vector_store
    
    async def evaluate_retrieval(
        self,
        test_cases: List[TestCase],
        k: int = 5
    ) -> Dict[str, float]:
        """
        ประเมินผล Retrieval
        
        Metrics:
        - Precision@K: TP / (TP + FP)
        - Recall@K: TP / (TP + FN)
        - MRR: Mean Reciprocal Rank
        - NDCG: Normalized Discounted Cumulative Gain
        - Hit Rate: % ที่มี relevant doc อย่างน้อย 1 อัน
        """
        precision_scores = []
        recall_scores = []
        reciprocal_ranks = []
        ndcg_scores = []
        hits = 0
        
        for test in test_cases:
            # Retrieve documents
            query_embedding = await self.embeddings.embed(test.query)
            retrieved_docs = await self.vector_store.search(
                query_embedding, 
                top_k=k
            )
            
            retrieved_ids = [doc["id"] for doc in retrieved_docs]
            relevant_ids = set(test.relevant_docs)
            
            # Calculate Precision@K
            if len(retrieved_ids) > 0:
                tp = len(set(retrieved_ids) & relevant_ids)
                precision = tp / len(retrieved_ids)
                precision_scores.append(precision)
            else:
                precision_scores.append(0.0)
            
            # Calculate Recall@K
            if len(relevant_ids) > 0:
                tp = len(set(retrieved_ids) & relevant_ids)
                recall = tp / len(relevant_ids)
                recall_scores.append(recall)
            else:
                recall_scores.append(0.0)
            
            # Calculate MRR
            rr = 0.0
            for i, doc_id in enumerate(retrieved_ids, 1):
                if doc_id in relevant_ids:
                    rr = 1.0 / i
                    hits += 1
                    break
            reciprocal_ranks.append(rr)
            
            # Calculate NDCG
            dcg = 0.0
            for i, doc_id in enumerate(retrieved_ids, 1):
                if doc_id in relevant_ids:
                    dcg += 1.0 / np.log2(i + 1)
            
            ideal_dcg = sum(1.0 / np.log2(i + 1) for i in range(1, min(len(relevant_ids), k) + 1))
            ndcg = dcg / ideal_dcg if ideal_dcg > 0 else 0.0
            ndcg_scores.append(ndcg)
        
        return {
            "precision_at_k": np.mean(precision_scores),
            "recall_at_k": np.mean(recall_scores),
            "mrr": np.mean(reciprocal_ranks),
            "ndcg": np.mean(ndcg_scores),
            "hit_rate": hits / len(test_cases),
        }
    
    async def evaluate_generation(
        self,
        test_cases: List[TestCase],
        generated_answers: List[str],
        retrieved_contexts: List[List[str]]
    ) -> Dict[str, float]:
        """
        ประเมินผล Generation ด้วย LLM-as-Judge
        
        Metrics:
        - Faithfulness: คำตอบตรงกับ context
        - Answer Relevance: คำตอบตรงกับคำถาม
        - Context Precision: Context มีประโยชน์
        - Context Recall: Context ครบถ้วน
        - Hallucination Rate: % ที่มีข้อมูลนอก context
        """
        faithfulness_scores = []
        relevance_scores = []
        context_precision_scores = []
        context_recall_scores = []
        hallucination_scores = []
        
        for test, answer, contexts in zip(
            test_cases, generated_answers, retrieved_contexts
        ):
            # Evaluate Faithfulness
            faithfulness = await self._evaluate_faithfulness(
                answer, contexts
            )
            faithfulness_scores.append(faithfulness)
            
            # Evaluate Answer Relevance
            relevance = await self._evaluate_relevance(
                test.query, answer
            )
            relevance_scores.append(relevance)
            
            # Evaluate Context Precision
            precision = await self._evaluate_context_precision(
                test.query, contexts
            )
            context_precision_scores.append(precision)
            
            # Evaluate Context Recall
            recall = await self._evaluate_context_recall(
                test.expected_answer, contexts
            )
            context_recall_scores.append(recall)
            
            # Detect Hallucination
            hallucination = await self._detect_hallucination(
                answer, contexts
            )
            hallucination_scores.append(hallucination)
        
        return {
            "faithfulness": np.mean(faithfulness_scores),
            "answer_relevance": np.mean(relevance_scores),
            "context_precision": np.mean(context_precision_scores),
            "context_recall": np.mean(context_recall_scores),
            "hallucination_rate": np.mean(hallucination_scores),
        }
    
    async def _evaluate_faithfulness(
        self,
        answer: str,
        contexts: List[str]
    ) -> float:
        """ประเมินว่าคำตอบตรงกับ context หรือไม่"""
        context_text = "\n".join(contexts)
        
        prompt = f"""ให้คะแนนความเที่ยงตรง (Faithfulness) ของคำตอบตาม context โดยให้คะแนนระหว่าง 0-1

Context:
{context_text}

คำตอบ:
{answer}

คำถาม:
1. คำตอบมีข้อมูลที่ไม่มีใน context หรือไม่?
2. คำตอบบิดเบือนข้อมูลจาก context หรือไม่?

ให้คะแนนเท่านั้น (0-1):"""
        
        try:
            result = await self.llm.complete(prompt)
            score = float(result.strip())
            return max(0, min(1, score))
        except:
            return 0.5
    
    async def _evaluate_relevance(
        self,
        query: str,
        answer: str
    ) -> float:
        """ประเมินว่าคำตอบตรงกับคำถามหรือไม่"""
        prompt = f"""ให้คะแนนความเกี่ยวข้อง (Relevance) ของคำตอบตามคำถาม โดยให้คะแนนระหว่าง 0-1

คำถาม:
{query}

คำตอบ:
{answer}

คำถาม:
1. คำตอบตอบคำถามที่ถามหรือไม่?
2. คำตอบครอบคลุมทุกส่วนของคำถามหรือไม่?

ให้คะแนนเท่านั้น (0-1):"""
        
        try:
            result = await self.llm.complete(prompt)
            score = float(result.strip())
            return max(0, min(1, score))
        except:
            return 0.5
    
    async def _evaluate_context_precision(
        self,
        query: str,
        contexts: List[str]
    ) -> float:
        """ประเมินว่า context ที่ดึงมามีประโยชน์หรือไม่"""
        if not contexts:
            return 0.0
        
        prompt = f"""ให้คะแนนความแม่นยำของ context (Context Precision) โดยให้คะแนนระหว่าง 0-1

คำถาม:
{query}

Context ที่ดึงมา:
{chr(10).join(f"- {ctx}" for ctx in contexts)}

คำถาม:
Context ที่ให้มาสามารถใช้ตอบคำถามได้หรือไม่?

ให้คะแนนเท่านั้น (0-1):"""
        
        try:
            result = await self.llm.complete(prompt)
            score = float(result.strip())
            return max(0, min(1, score))
        except:
            return 0.5
    
    async def _evaluate_context_recall(
        self,
        expected_answer: str,
        contexts: List[str]
    ) -> float:
        """ประเมินว่า context ครบถ้วนหรือไม่"""
        context_text = "\n".join(contexts)
        
        prompt = f"""ให้คะแนนความครบถ้วนของ context (Context Recall) โดยให้คะแนนระหว่าง 0-1

คำตอบที่ถูกต้อง:
{expected_answer}

Context ที่ดึงมา:
{context_text}

คำถาม:
Context มีข้อมูลครบถ้วนที่จะตอบได้ตามคำตอบที่ถูกต้องหรือไม่?

ให้คะแนนเท่านั้น (0-1):"""
        
        try:
            result = await self.llm.complete(prompt)
            score = float(result.strip())
            return max(0, min(1, score))
        except:
            return 0.5
    
    async def _detect_hallucination(
        self,
        answer: str,
        contexts: List[str]
    ) -> float:
        """ตรวจจับ hallucination (0 = ไม่มี, 1 = มีมาก)"""
        context_text = "\n".join(contexts)
        
        prompt = f"""ตรวจสอบว่าคำตอบมี Hallucination (ข้อมูลที่ไม่มีใน context) หรือไม่

Context:
{context_text}

คำตอบ:
{answer}

มีข้อมูลในคำตอบที่ไม่มีใน context หรือไม่? (0 = ไม่มีเลย, 1 = มีมาก)

ให้คะแนนเท่านั้น (0-1):"""
        
        try:
            result = await self.llm.complete(prompt)
            score = float(result.strip())
            return max(0, min(1, score))
        except:
            return 0.0
    
    async def evaluate_thai_specific(
        self,
        test_cases: List[TestCase],
        generated_answers: List[str]
    ) -> Dict[str, float]:
        """
        ประเมินผลเฉพาะสำหรับภาษาไทย
        """
        # ใช้ PyThaiNLP สำหรับ tokenization score
        try:
            from pythainlp.tokenize import word_tokenize
            
            tokenization_scores = []
            for answer in generated_answers:
                # ตรวจสอบว่า tokenization สมเหตุสมผลหรือไม่
                tokens = word_tokenize(answer, engine="newmm")
                # คำนวณ score จากความยาวเฉลี่ยของ token
                avg_token_length = sum(len(t) for t in tokens) / len(tokens) if tokens else 0
                # ค่าปกติควรอยู่ระหว่าง 2-10 ตัวอักษรต่อ token
                score = 1.0 - abs(avg_token_length - 6) / 6
                tokenization_scores.append(max(0, min(1, score)))
        except:
            tokenization_scores = [0.5] * len(generated_answers)
        
        # คำนวณ semantic similarity สำหรับภาษาไทย
        semantic_scores = []
        for test, answer in zip(test_cases, generated_answers):
            try:
                # ใช้ embedding สำหรับ Thai
                expected_emb = await self.embeddings.embed(test.expected_answer)
                answer_emb = await self.embeddings.embed(answer)
                
                # คำนวณ cosine similarity
                similarity = np.dot(expected_emb, answer_emb) / (
                    np.linalg.norm(expected_emb) * np.linalg.norm(answer_emb)
                )
                semantic_scores.append(max(0, similarity))
            except:
                semantic_scores.append(0.5)
        
        return {
            "thai_tokenization_score": np.mean(tokenization_scores),
            "thai_semantic_similarity": np.mean(semantic_scores),
        }
    
    async def run_full_evaluation(
        self,
        test_cases: List[TestCase],
        rag_system
    ) -> Dict[str, Any]:
        """
        รันการประเมินผลแบบครบวงจร
        """
        start_time = datetime.now()
        
        # Run retrieval evaluation
        retrieval_metrics = await self.evaluate_retrieval(test_cases)
        
        # Generate answers for each test case
        generated_answers = []
        retrieved_contexts = []
        response_times = []
        
        for test in test_cases:
            query_start = datetime.now()
            
            # Run RAG query
            result = await rag_system.query(test.query)
            
            query_time = (datetime.now() - query_start).total_seconds()
            response_times.append(query_time)
            
            generated_answers.append(result["answer"])
            retrieved_contexts.append(result["contexts"])
        
        # Run generation evaluation
        generation_metrics = await self.evaluate_generation(
            test_cases, generated_answers, retrieved_contexts
        )
        
        # Run Thai-specific evaluation
        thai_metrics = await self.evaluate_thai_specific(
            test_cases, generated_answers
        )
        
        # Calculate accuracy
        accuracy_scores = []
        for test, answer in zip(test_cases, generated_answers):
            # ใช้ LLM เปรียบเทียบคำตอบ
            accuracy = await self._calculate_accuracy(
                test.expected_answer, answer
            )
            accuracy_scores.append(accuracy)
        
        # Compile all metrics
        metrics = EvaluationMetrics(
            **retrieval_metrics,
            **generation_metrics,
            **thai_metrics,
            accuracy=np.mean(accuracy_scores),
            response_time=np.mean(response_times),
        )
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "metrics": metrics.to_dict(),
            "overall_score": metrics.get_overall_score(),
            "test_cases_evaluated": len(test_cases),
            "evaluation_time": total_time,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _calculate_accuracy(
        self,
        expected: str,
        actual: str
    ) -> float:
        """คำนวณความถูกต้องโดยใช้ LLM เปรียบเทียบ"""
        prompt = f"""เปรียบเทียบคำตอบ 2 อันนี้ว่าตรงกันหรือไม่ ให้คะแนน 0-1

คำตอบที่ถูกต้อง:
{expected}

คำตอบที่ได้:
{actual}

ให้คะแนนเท่านั้น (0-1):"""
        
        try:
            result = await self.llm.complete(prompt)
            score = float(result.strip())
            return max(0, min(1, score))
        except:
            return 0.5
    
    def compare_with_baseline(
        self,
        current_metrics: Dict[str, float],
        baseline_metrics: Dict[str, float],
        threshold: float = 0.1
    ) -> Dict[str, Any]:
        """
        เปรียบเทียบผลกับ baseline
        """
        changes = {}
        drifts = []
        
        for metric, baseline in baseline_metrics.items():
            current = current_metrics.get(metric, 0)
            change = current - baseline
            change_percent = (change / baseline * 100) if baseline > 0 else 0
            
            changes[metric] = {
                "baseline": baseline,
                "current": current,
                "change": change,
                "change_percent": change_percent,
            }
            
            # Detect drift
            if abs(change) > threshold:
                drifts.append({
                    "metric": metric,
                    "change": change,
                    "severity": "high" if abs(change) > 0.2 else "medium",
                })
        
        return {
            "changes": changes,
            "drifts": drifts,
            "has_drift": len(drifts) > 0,
        }


# Test Dataset สำหรับ HR Domain
HR_TEST_DATASET = [
    TestCase(
        id="hr_001",
        query="นโยบายลาพักร้อนของบริษัทเป็นอย่างไร?",
        query_type="easy",
        expected_answer="พนักงานมีสิทธิ์ลาพักร้อนได้ 6 วันทำงานต่อปี สำหรับพนักงานที่ทำงานครบ 1 ปี",
        relevant_docs=["doc_policy_001", "doc_handbook_003"],
        expected_contexts=["นโยบายการลาพักร้อน: พนักงานมีสิทธิ์ลาพักร้อน 6 วันต่อปี"],
        category="hr_policy",
    ),
    TestCase(
        id="hr_002",
        query="วิธีการขอลาป่วยฉุกเฉินนอกเวลาทำการต้องทำอย่างไร?",
        query_type="complex",
        expected_answer="ติดต่อผู้บังคับบัญชาทันทีทางโทรศัพท์ หรือส่งข้อความผ่านช่องทางที่บริษัทกำหนด แล้วต้องยื่นใบลาป่วยภายใน 3 วันทำการ",
        relevant_docs=["doc_policy_002", "doc_procedure_001"],
        expected_contexts=["กรณีลาป่วยฉุกเฉิน", "แจ้งผู้บังคับบัญชา", "ยื่นใบลาภายใน 3 วัน"],
        category="hr_policy",
    ),
    TestCase(
        id="hr_003",
        query="พนักงานใหม่ที่ยังไม่ครบ 1 ปีมีสิทธิ์ลาพักร้อนหรือไม่?",
        query_type="edge_case",
        expected_answer="พนักงานใหม่ที่ยังไม่ครบ 1 ปี ยังไม่มีสิทธิ์ลาพักร้อน แต่สามารถใช้ลากิจได้ตามสิทธิ",
        relevant_docs=["doc_policy_001", "doc_faq_005"],
        expected_contexts=["พนักงานใหม่", "ยังไม่ครบ 1 ปี", "ไม่มีสิทธิ์ลาพักร้อน"],
        category="hr_policy",
    ),
    TestCase(
        id="hr_004",
        query="เงินเดือน CEO ของบริษัทเป็นเท่าไหร่?",
        query_type="out_of_scope",
        expected_answer="ข้อมูลนี้เป็นความลับของบริษัท และไม่มีในเอกสารที่ระบบเข้าถึงได้",
        relevant_docs=[],
        expected_contexts=[],
        category="general",
    ),
    TestCase(
        id="hr_005",
        query="สรุปสิทธิประโยชน์ด้านสุขภาพและวิธีการใช้งาน",
        query_type="multi_hop",
        expected_answer="พนักงานมีสิทธิประโยชน์ด้านสุขภาพ ได้แก่ ประกันสุขภาพกลุ่ม, ตรวจสุขภาพประจำปี, และค่ารักษาพยาบาล โดยต้องแจ้งฝ่าย HR เพื่อใช้สิทธิ",
        relevant_docs=["doc_benefits_001", "doc_benefits_002", "doc_procedure_003"],
        expected_contexts=["ประกันสุขภาพกลุ่ม", "ตรวจสุขภาพ", "ค่ารักษาพยาบาล", "แจ้งฝ่าย HR"],
        category="benefits",
    ),
]
