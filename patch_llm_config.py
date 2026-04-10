import re
with open('/opt/AgentEducator2/backend/config/unified_llm_config.py', 'r', encoding='utf-8') as f:
    text = f.read()

if 'self._models["qa"] =' not in text:
    text = text.replace(
        'self._models["qa_main"] = LLMModelConfig(',
        'self._models["qa"] = LLMModelConfig(\n            model_name="doubao-seed-1-8-251228",\n            provider=LLMProvider.VOLCENGINE,\n            endpoint_key="volcengine_doubao",\n            default_params={"temperature": 0.5, "max_tokens": 4096, "timeout": 36000},\n            description="qa fallback"\n        )\n        self._models["qa_main"] = LLMModelConfig('
    )
    with open('/opt/AgentEducator2/backend/config/unified_llm_config.py', 'w', encoding='utf-8') as f:
        f.write(text)
    import os
    os.system('pm2 restart all')
    os.system('systemctl restart gunicorn')
    print("Done patching backend.")
