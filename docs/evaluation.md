# LLM Evaluation Module - HR-RAG

> ระบบประเมินผล RAG ตามมาตรฐาน RAGAS และ Custom Metrics สำหรับภาษาไทย

## 🎯 Overview

โมดูลนี้ใช้สำหรับประเมินประสิทธิภาพของ RAG System ครอบคลุมทั้ง:
- **Retrieval Metrics** - วัดผลการค้นหาเอกสาร
- **Generation Metrics** - วัดผลการสร้างคำตอบ
- **Thai-specific Metrics** - วัดผลเฉพาะสำหรับภาษาไทย

## 📊 Metrics ที่รองรับ

### Retrieval Metrics

| Metric | Description | Target (HR) |
|--------|-------------|-------------|
| **Precision@K** | % เอกสารที่ดึงมาที่เกี่ยวข้องจริง | ≥ 0.85 |
| **Recall@K** | % เอกสารที่เกี่ยวข้องที่ถูกดึงมา | ≥ 0.80 |
| **MRR** | Mean Reciprocal Rank | ≥ 0.75 |
| **NDCG** | Normalized DCG | ≥ 0.80 |
| **Hit Rate** | % ที่มี relevant doc อย่างน้อย 1 อัน | ≥ 0.90 |

### Generation Metrics

| Metric | Description | Target (HR) |
|--------|-------------|-------------|
| **Faithfulness** | คำตอบตรงกับ context | ≥ 0.90 |
| **Answer Relevance** | คำตอบตรงกับคำถาม | ≥ 0.85 |
| **Context Precision** | Context ที่ให้มีประโยชน์ | ≥ 0.80 |
| **Context Recall** | Context ครบถ้วน | ≥ 0.75 |
| **Hallucination Rate** | % ที่มีข้อมูลนอก context | ≤ 0.05 |

### Thai-specific Metrics

| Metric | Description |
|--------|-------------|
| **Thai Tokenization Score** | คะแนนการตัดคำภาษาไทย |
| **Thai Semantic Similarity** | ความคล้ายคลึงเชิงความหมาย |

## 🚀 API Endpoints

### Run Evaluation
```http
POST /api/evaluation/run
Authorization: Bearer <token>
Content-Type: application/json

{
  "provider": "openai",
  "test_dataset": "hr_default",
  "k": 5
}
```

**Response:**
```json
{
  "evaluation_id": "eval_20260307_143022_1",
  "metrics": {
    "precision_at_k": 0.87,
    "recall_at_k": 0.82,
    "mrr": 0.78,
    "ndcg": 0.83,
    "hit_rate": 0.92,
    "faithfulness": 0.91,
    "answer_relevance": 0.86,
    "context_precision": 0.84,
    "context_recall": 0.79,
    "hallucination_rate": 0.03,
    "accuracy": 0.88,
    "response_time": 1.45,
    "thai_tokenization_score": 0.92,
    "thai_semantic_similarity": 0.85
  },
  "overall_score": 0.856,
  "test_cases_evaluated": 5,
  "evaluation_time": 12.34,
  "timestamp": "2026-03-07T14:30:22",
  "provider": "openai"
}
```

### Get Dashboard
```http
GET /api/evaluation/dashboard
Authorization: Bearer <token>
```

### Compare Evaluations
```http
POST /api/evaluation/compare
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_evaluation_id": "eval_20260307_143022_1",
  "baseline_evaluation_id": "eval_20260306_100000_1"
}
```

### Get Target Metrics
```http
GET /api/evaluation/metrics/targets
```

## 🧪 Test Dataset

ชุดทดสอบ `HR_TEST_DATASET` ประกอบด้วย:

### Query Types

1. **Easy Queries**
   - "นโยบายลาพักร้อนของบริษัทเป็นอย่างไร?"

2. **Complex Queries**
   - "วิธีการขอลาป่วยฉุกเฉินนอกเวลาทำการต้องทำอย่างไร?"

3. **Edge Cases**
   - "พนักงานใหม่ที่ยังไม่ครบ 1 ปีมีสิทธิ์ลาพักร้อนหรือไม่?"

4. **Out of Scope**
   - "เงินเดือน CEO ของบริษัทเป็นเท่าไหร่?"

5. **Multi-hop**
   - "สรุปสิทธิประโยชน์ด้านสุขภาพและวิธีการใช้งาน"

### Categories
- `hr_policy` - นโยบาย HR
- `benefits` - สวัสดิการ
- `legal` - กฎหมายแรงงาน
- `general` - ทั่วไป

## 📈 Evaluation Dashboard (Frontend)

เข้าถึงที่: `http://localhost:3000/evaluation`

### Features
- แสดง Overall Score และ Metrics ทั้งหมด
- แสดง Trends เปรียบเทียบกับครั้งก่อน
- รัน Evaluation ใหม่ได้ทันที
- เปรียบเทียบกับ Baseline
- แสดงค่าเป้าหมายตาม Use Case

## 🔄 Drift Detection

ระบบจะตรวจจับ Performance Drift เมื่อ:
- Metric เปลี่ยนแปลง > 10% จาก baseline
- ระบบจะแจ้งเตือนและให้คำแนะนำในการแก้ไข

### ตัวอย่าง Recommendations

| ปัญหา | คำแนะนำ |
|-------|----------|
| Precision ต่ำ | ปรับปรุง embedding model หรือใช้ re-ranking |
| Recall ต่ำ | เพิ่ม chunk overlap หรือใช้ hybrid search |
| Faithfulness ต่ำ | ปรับปรุง prompt หรือลด context length |
| Hallucination สูง | ใช้ stricter prompting |

## 🛠️ การเพิ่ม Custom Test Cases

```python
from app.services.evaluation import TestCase

custom_tests = [
    TestCase(
        id="custom_001",
        query="คำถามของคุณ",
        query_type="complex",
        expected_answer="คำตอบที่ถูกต้อง",
        relevant_docs=["doc_001"],
        expected_contexts=["context ที่ควรได้"],
        category="hr_policy",
    ),
]
```

## 📊 การตีความผลลัพธ์

### Overall Score
- **≥ 0.90** - Excellent 🟢
- **0.75 - 0.89** - Good 🟡
- **0.60 - 0.74** - Fair 🟠
- **< 0.60** - Needs Improvement 🔴

### ตัวอย่างผลลัพธ์

```
Evaluation Summary
==================
Overall Score: 85.6% ✅

Retrieval Metrics:
  Precision@K: 87% ✅ (Target: ≥85%)
  Recall@K: 82% ✅ (Target: ≥80%)
  MRR: 78% ✅
  NDCG: 83% ✅
  Hit Rate: 92% ✅

Generation Metrics:
  Faithfulness: 91% ✅ (Target: ≥90%)
  Answer Relevance: 86% ✅ (Target: ≥85%)
  Hallucination Rate: 3% ✅ (Target: ≤5%)

Thai Metrics:
  Tokenization: 92% ✅
  Semantic Similarity: 85% ✅

Response Time: 1.45s ✅ (Target: ≤2s)
```

## 🔗 Integration with CI/CD

```yaml
# .github/workflows/evaluation.yml
name: RAG Evaluation

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # รันทุกสัปดาห์

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Evaluation
        run: |
          curl -X POST http://api/evaluation/run \
            -H "Authorization: Bearer ${{ secrets.API_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{"provider": "openai", "test_dataset": "hr_default"}'
```

## 📚 References

- [RAGAS Documentation](https://docs.ragas.io/)
- [LangChain Evaluation](https://python.langchain.com/docs/guides/evaluation/)
- [RAG Benchmark](https://github.com/arize-ai/RAG-benchmark)

---

*พัฒนาโดย Lita ✨ สำหรับ HR-RAG System*
