# Memory Exporter

ส่งออกความทรงจำไปยัง AI Platform อื่น (Export memories to other AI platforms)

## Supported Platforms
- ✅ OpenAI / ChatGPT
- ✅ Claude / Anthropic
- ✅ Google Gemini
- ✅ LangChain Memory
- ✅ Generic JSON
- ✅ Markdown Document

## Features
- Export conversations to multiple formats
- Filter by tags
- Include/exclude metadata
- Validate before export

## Functions
- `export_memories()` - ส่งออกความทรงจำ
- `get_supported_platforms()` - แสดงแพลตฟอร์มที่รองรับ
- `validate_export()` - ตรวจสอบข้อมูลก่อนส่งออก

## Example
```python
result = export_memories(
    memories=memories,
    target_platform="openai",
    include_metadata=True
)
```

## Author
HR-RAG Team

## Version
1.0.0
